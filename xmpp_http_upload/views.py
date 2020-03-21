# -*- coding: utf-8 -*-
#
# This file is part of django-xmpp-http-upload (https://github.com/mathiasertl/django-xmpp-http-upload).
#
# django-xmpp-http-upload is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-xmpp-http-upload is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with django-xmpp-http-upload. If
# not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import json
import re

from django.conf import settings
from django.db.models import Sum
from django.http import FileResponse
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import UnreadablePostError
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import get_valid_filename
from django.views.generic.base import View

from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Upload
from .utils import get_config
from .utils import ws_download

_upload_base = getattr(settings, 'XMPP_HTTP_UPLOAD_ROOT', 'http_upload')


def _add_content_length():
    return getattr(settings, 'XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH', False)


# regex of ascii control chars:
control_chars = ''.join(map(chr, list(range(0, 32)) + list(range(127, 160))))
control_char_re = re.compile('[%s]' % re.escape(control_chars))


class RequestSlotView(View):
    http_method_names = {'get', }

    # TODO: do some general checks (e.g. origin of request?) in the dispatch method

    def get(self, request, *args, **kwargs):
        try:
            jid = request.GET['jid']  # jid of the uploader
            name = get_valid_filename(request.GET['name'])  # filename
            size = int(request.GET['size'])  # filesize

            # type is optional:
            content_type = request.GET.get('type')
        except (KeyError, IndexError, ValueError):
            return HttpResponse(status=400)

        if not jid or not size or not name or size <= 0:
            return HttpResponse("Empty JID or size passed.", status=400)
        if '/' in name:  # pragma: no cover - assured by get_valid_filename, but just to be sure
            return HttpResponseForbidden('No slashes in filenames allowed.')

        # replace control characters from jid and name, just to be sure
        jid = control_char_re.sub('', jid)
        name = control_char_re.sub('', name)

        # shortcuts
        now = timezone.now()
        qs = Upload.objects.filter(jid=jid)

        # TODO: Exclude expired slots (client requested slot but did not upload a file) here.

        config = get_config(jid)

        # If the config is set to False, everything should be denied.
        if config is False:
            return HttpResponseForbidden("You are not allowed to upload files.")

        # deny if file is to large
        if 'max_file_size' in config and size > config['max_file_size']:
            message = 'Files may not be larger than %s bytes.' % config['max_file_size']
            return HttpResponse(message, status=413)

        # deny if total size of uploaded files is too large
        if 'max_total_size' in config:
            message = 'User may not upload more than %s bytes.' % config['max_total_size']

            uploaded = qs.aggregate(total=Sum('size'))
            if uploaded['total'] is None:  # no uploads by this user yet
                uploaded['total'] = 0
            if uploaded['total'] + size > config['max_total_size']:
                return HttpResponseForbidden(message)

        if 'bytes_per_timedelta' in config:
            delta = config['bytes_per_timedelta']['delta']
            quota = config['bytes_per_timedelta']['bytes']
            uploaded = qs.filter(created__gt=now - delta).aggregate(total=Sum('size'))
            if uploaded['total'] is None:  # no uploads by this user yet
                uploaded['total'] = 0

            if uploaded['total'] + size > quota:
                return HttpResponse("User is temporarily out of quota.", status=402)

        if 'uploads_per_timedelta' in config:
            delta = config['uploads_per_timedelta']['delta']
            quota = config['uploads_per_timedelta']['uploads']
            if qs.filter(created__gt=now - delta).count() + 1 > quota:
                return HttpResponse("User is temporarily out of quota.", status=402)

        hash = get_random_string(32)
        upload = Upload(jid=jid, name=name, size=size, type=content_type, hash=hash)

        # Test if the filename is to long. Djangos FileField silently truncates to max_length,
        # so if the filename is too long, users will get a HTTP 404 when downloading the file.
        file_field = Upload._meta.get_field('file')
        if len(file_field.upload_to(upload, name)) > file_field.max_length:
            message = 'Filename must not be longer then %s characters.' % file_field.max_length
            return HttpResponse(message, status=413)

        put_url, get_url = upload.get_urls(request)

        output = request.GET.get('output', 'text/plain')
        if output == 'text/plain':
            content = '%s\n%s' % (put_url, get_url)
        elif output == 'application/json':
            content = json.dumps({'get': get_url, 'put': put_url})
        else:
            return HttpResponse("Unsupported content type in output.", status=400)

        # Finally sure we will have a response, so save upload to database.
        upload.save()

        response = HttpResponse(content, content_type=output)
        if _add_content_length() is True:
            response['Content-Length'] = len(content)
        return response


class MaxSizeView(View):
    def get(self, request):
        try:
            jid = request.GET['jid']  # jid of the uploader
        except (KeyError):
            return HttpResponse('"jid" is a required GET parameter.', status=400)

        config = get_config(jid)
        if config is False:
            return HttpResponseForbidden("You are not allowed to upload files.")

        size = int(config.get('max_file_size', 0))

        # get output type
        output = request.GET.get('output', 'text/plain')
        if output == 'text/plain':
            content = str(size)
        elif output == 'application/json':
            content = json.dumps({'max_size': size})
        else:
            return HttpResponse("Unsupported content type in output.", status=400)

        response = HttpResponse(content, content_type=output)
        if _add_content_length() is True:
            response['Content-Length'] = len(content)
        return response


class UploadView(APIView):
    parser_classes = (FileUploadParser, )

    def get(self, request, hash, filename):
        """Download a file."""
        if ws_download() is True:
            return HttpResponseForbidden()
        upload = Upload.objects.uploaded().get(hash=hash, name=filename)

        resp = FileResponse(upload.file, content_type=upload.type, filename=filename)
        resp['Content-Length'] = upload.file.size
        return resp

    def put(self, request, hash, filename):
        try:
            upload = Upload.objects.for_upload().get(hash=hash, name=filename)
        except Upload.DoesNotExist:
            return HttpResponseForbidden()
        content_type = request.META.get('CONTENT_TYPE', 'application/octet-stream')

        if int(request.META.get('CONTENT_LENGTH', -1)) != upload.size:
            return HttpResponse("File size (%s) does not match requested size (%s)." % (
                request.META['CONTENT_LENGTH'], upload.size),
                status=400)
        if upload.type is not None and content_type != upload.type:
            return HttpResponse(
                'Content type (%s) does not match requested type.' % request.META['CONTENT_TYPE'],
                status=400)

        try:
            file_obj = request.FILES['file']
        except UnreadablePostError:  # pragma: no cover
            # This seems to happen if the client never actually posts any data.
            # Django docs: "UnreadablePostError is raised when a user cancels an upload."
            return HttpResponse('Could not read post request.', status=400)

        upload.file = file_obj
        upload.type = content_type
        upload.save()
        return Response(status=201)

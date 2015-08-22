# -*- coding: utf-8 -*-
#
# This file is part of django-xmpp-http-upload
# (https://github.com/mathiasertl/django-xmpp-http-upload).
#
# django-xmpp-http-upload is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# django-xmpp-http-upload is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# django-xmpp-http-upload.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import json

from django.conf import settings
from django.http import HttpResponse
from django.http import FileResponse
from django.utils.crypto import get_random_string
from django.utils.six.moves.urllib.parse import urlsplit
from django.views.generic.base import View

from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Upload

_upload_base = getattr(settings, 'XMPP_HTTP_UPLOAD_ROOT', 'http_upload')


class RequestSlotView(View):
    http_method_names = {'get', 'post', }

    # TODO: do some general checks (e.g. origin of request?) in the dispatch method

    def get(self, request, *args, **kwargs):
        try:
            jid = request.GET['jid']  # jid of the uploader
            name = request.GET['name']  # filename
            size = int(request.GET['size'])  # filesize

            # type is optional:
            content_type = request.GET.get('type')
        except (KeyError, IndexError, ValueError):
            return HttpResponse(status=400)

        if not jid or not size or not name or size <= 0:
            return HttpResponse("Empty JID or size passed.", status=400)

        # TODO: Check quotas, permissions, etc

        hash = get_random_string(64)
        upload = Upload.objects.create(jid=jid, name=name, size=size, type=content_type, hash=hash)

        location = upload.get_absolute_url()
        base = getattr(settings, 'XMPP_HTTP_UPLOAD_URL_BASE', None)
        if base is None:
            put_url = request.build_absolute_uri(location)
        else:
            put_url = '%s%s' % (base, location)

        ws_download = getattr(settings, 'XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD', True)
        if ws_download is True:
            get_url = '%s%s/%s/%s' % (settings.MEDIA_URL, _upload_base.strip('/'),
                                      upload.hash, upload.name)
            if not urlsplit(get_url).netloc:
                if base is None:
                    get_url = request.build_absolute_uri(get_url)
                else:
                    get_url = '%s%s' % (base, get_url)

        else:
            get_url = put_url

        output = request.GET.get('output', 'text/plain')
        if output == 'text/plain':
            return HttpResponse('%s\n%s' % (put_url, get_url), content_type=output)
        elif output == 'application/json':
            content = json.dumps({'get': get_url, 'put': put_url})
            return HttpResponse(content, content_type=output)
        # TODO: Support XML as output format (certainly useful b/c XMPP servers already need to
        #       have support for XML
        else:
            return HttpResponse("Unsupported content type in output.", status=400)


class UploadView(APIView):
    parser_classes = (FileUploadParser, )

    def get(self, request, hash, filename):
        """Download a file."""
        upload = Upload.objects.uploaded().get(hash=hash, name=filename)

        return FileResponse(upload.file, content_type=upload.type)

    def put(self, request, hash, filename, format=None):
        upload = Upload.objects.for_upload().get(hash=hash, name=filename)
        content_type = request.META.get('CONTENT_TYPE', 'application/octet-stream')

        if int(request.META['CONTENT_LENGTH']) != upload.size:
            return HttpResponse(
                "File size (%s) does not match requested size." % request.META['CONTENT_LENGTH'],
                status=400)
        if upload.type is not None and content_type != upload.type:
            return HttpResponse(
                'Content type (%s) does not match requested type.' % request.META['CONTENT_TYPE'],
                status=400)

        file_obj = request.data['file']
        upload.file = file_obj
        upload.type = content_type
        upload.save()
        return Response(status=201)

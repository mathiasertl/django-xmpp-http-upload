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

from django.conf import settings
from django.http import HttpResponse
from django.http import FileResponse
from django.utils.crypto import get_random_string
from django.views.generic.base import View

from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Upload


class RequestSlotView(View):
    http_method_names = {'get', 'post', }

    # TODO: do some general checks (e.g. origin of request?) in the dispatch method

    def get(self, request, *args, **kwargs):
        try:
            jid = request.GET['jid'][0]
            size = int(request.GET['size'][0])

            # type is optional:
            content_type = request.GET.get('type')
            if content_type:
                content_type = content_type[0]
        except (KeyError, IndexError, ValueError):
            return HttpResponse(status=400)

        if not jid or not size or size <= 0:  # empty jid or size passed
            return HttpResponse(status=400)

        # TODO: Check quotas, permissions, etc

        hash = get_random_string(64)
        upload = Upload.objects.create(jid=jid, size=size, type=content_type, hash=hash)

        location = upload.get_absolute_url()
        domain = getattr(settings, 'XMPP_HTTP_UPLOAD_DOMAIN', None)
        if domain is None:
            url = request.build_absolute_uri(location)
        else:
            url = '%s%s' % (domain, location)

        return HttpResponse('%s\n%s' % (url, url))


class UploadView(APIView):
    parser_classes = (FileUploadParser, )

    def get(self, request, hash, filename):
        """Download a file."""
        upload = Upload.objects.get(hash=hash, filename=filename)

        return FileResponse(upload.file)

    def put(self, request, hash, filename, format=None):
        upload = Upload.objects.get(hash=hash, filename=filename)

        # TODO: check size

        file_obj = request.data['file']
        upload.file = file_obj
        upload.save()
        return Response(status=204)

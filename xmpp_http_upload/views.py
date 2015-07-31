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

from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.views.generic.base import View

from .models import Upload


class RequestSlotView(View):
    http_method_names = {'get', 'post', }

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

        if not jid or not size or size <= 0:  # empty jid or size passed23
            return HttpResponse(status=400)

        hash = get_random_string(64)
        upload = Upload.objects.create(jid=jid, size=size, type=content_type, hash=hash)

        return HttpResponse(upload.hash)

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

import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.six.moves.urllib.parse import quote
from django.utils.six.moves.urllib.parse import urlsplit

from .querysets import UploadQuerySet

_upload_base = getattr(settings, 'XMPP_HTTP_UPLOAD_ROOT', 'http_upload')
_ws_download = getattr(settings, 'XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD', True)
_force_https = getattr(settings, 'XMPP_HTTP_UPLOAD_URL_HTTPS', False)
_upload_url = getattr(settings, 'XMPP_HTTP_UPLOAD_URL_BASE', None)


def get_upload_path(instance, filename):
    return os.path.join(_upload_base, instance.hash, filename)


class Upload(models.Model):
    objects = UploadQuerySet.as_manager()

    # housekeeping
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Populated when a slot is requested
    jid = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    size = models.PositiveIntegerField()
    type = models.CharField(max_length=255, null=True, blank=True)
    hash = models.CharField(max_length=64)

    # Populated when the file is uploaded
    file = models.FileField(upload_to=get_upload_path, null=True, blank=True, max_length=255)
    uploaded = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('xmpp-http-upload:share',
                       kwargs={'hash': self.hash, 'filename': self.name})

    def get_urls(self, request):
        location = self.get_absolute_url()
        if _upload_url is None:
            put_url = request.build_absolute_uri(location)
        else:
            put_url = '%s%s' % (_upload_url, location)

        if _ws_download is True:
            get_url = '%s%s/%s/%s' % (settings.MEDIA_URL, _upload_base.strip('/'), self.hash,
                                      quote(self.name.encode('utf-8')))

            if not urlsplit(get_url).netloc:
                if _upload_url is None:
                    get_url = request.build_absolute_uri(get_url)
                else:
                    get_url = '%s%s' % (_upload_url, get_url)

        else:
            get_url = put_url

        if _force_https is True:
            put_url = put_url.replace('http://', 'https://')
            get_url = get_url.replace('http://', 'https://')

        return put_url, get_url

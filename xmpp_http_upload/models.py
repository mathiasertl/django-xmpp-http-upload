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

from django.db import models
from django.core.urlresolvers import reverse


class Upload(models.Model):
    # housekeeping
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Populated when a slot is requested
    jid = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    size = models.PositiveIntegerField()
    type = models.CharField(max_length=64, null=True, blank=True)
    hash = models.CharField(max_length=64)

    # Populated when the file is uploaded
    file = models.FileField(upload_to='http_upload', null=True, blank=True)
    uploaded = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('xmpp-http-upload:share',
                       kwargs={'hash': self.hash, 'filename': self.file})

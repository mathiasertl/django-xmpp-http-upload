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
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

_put_timeout = timedelta(seconds=int(getattr(settings, 'XMPP_HTTP_UPLOAD_PUT_TIMEOUT', 360)))
_share_timeout = timedelta(seconds=int(
    getattr(settings, 'XMPP_HTTP_UPLOAD_SHARE_TIMEOUT', 86400 * 30)))


class UploadQuerySet(models.QuerySet):
    def for_upload(self):
        expired = timezone.now() - _put_timeout
        return self.filter(file='', created__gt=expired)

    def expired(self):
        expired = timezone.now() - _put_timeout
        return self.filter(file='', created__lt=expired)

    def uploaded(self):
        return self.exclude(file='')

    def cleanup(self, slots=True, files=True, timeout=None):
        # Just remove expired keys
        if slots is True:
            self.expired().delete()

        if files is True:
            if timeout is None:
                timeout = _share_timeout
            else:
                timeout = timedelta(seconds=timeout)

            expired = timezone.now() - timeout
            queryset = self.filter(created__lt=expired)
            for instance in queryset:
                path = os.path.dirname(instance.file.path)
                instance.file.delete(save=False)  # files are deleted anyway ;-)

                # remove any remaining empty directories
                if os.path.exists(path) and not os.listdir(path):
                    os.rmdir(path)
            queryset.delete()

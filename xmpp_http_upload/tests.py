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

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase
from django.utils import timezone

from .models import Upload

user_jid = 'example@example.net'

class RequestSlotTestCase(TestCase):
    def _slot(self, **kwargs):
        url = reverse('xmpp-http-upload:slot')
        c = Client()
        return c.get(url, kwargs)

    def test_slot(self):
        response = self._slot(jid='admin@example.com', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

    def test_blocked(self):
        response = self._slot(jid='blocked@jabber.at', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 0)

    def test_max_file_size(self):
        response = self._slot(jid=user_jid, name='example.jpg', size=1024 * 1024)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 0)

        response = self._slot(jid=user_jid, name='example.jpg', size=300 * 1024)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

    def test_max_total_size(self):
        # first, create some uploads manually so we're almost at the limit
        for i in range(1, 11):
            Upload.objects.create(jid=user_jid, name='example%s.jpg' % i, size=300 * 1024)

        # created is auto_now, and we cannot override it, but we can update it
        Upload.objects.update(created=timezone.now() - timedelta(hours=2))

        # now we would be over quota
        response = self._slot(jid=user_jid, name='example%s.jpg' % i, size=300 * 1024)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 10)

    def test_bytes_per_timedelta(self):
        # First, upload to files totalling 800 KB
        for i in range(1, 3):
            response = self._slot(jid=user_jid, name='example%s.jpg' % i, size=400 * 1024)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(Upload.objects.count(), i)
        self.assertEquals(Upload.objects.count(), i)

        # next slot would exceed bytes_per_timedelta, but not uploads_per_timedelta
        response = self._slot(jid=user_jid, name='example%s.jpg' % (i + 1), size=400 * 1024)
        self.assertEquals(response.status_code, 402)
        self.assertEquals(Upload.objects.count(), i)

    def test_uploads_per_timedelta(self):
        # first, create some uploads manually so we're almost at the limit
        for i in range(1, 4):
            response = self._slot(jid=user_jid, name='example%s.jpg' % i, size=10 * 1024)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(Upload.objects.count(), i)
        self.assertEquals(Upload.objects.count(), i)

        response = self._slot(jid=user_jid, name='example%s.jpg' % (i + 1), size=10 * 1024)
        self.assertEquals(response.status_code, 402)
        self.assertEquals(Upload.objects.count(), i)

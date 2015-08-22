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

from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase
#from django.utils.six.moves.urllib.parse import urlencode

from .models import Upload


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

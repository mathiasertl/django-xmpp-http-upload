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
from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.utils import six
from django.utils import timezone
from django.utils.six.moves.urllib.parse import urlsplit

from .models import Upload

user_jid = 'example@example.net'


def slot(**kwargs):
    url = reverse('xmpp-http-upload:slot')
    c = Client()
    return c.get(url, kwargs)


def put(path, data, content_type='application/octet-stream', **kwargs):
    c = Client()
    return c.put(path, data, content_type=content_type)


def get(path):
    c = Client()
    return c.get(path)


class RequestSlotTestCase(TestCase):
    def test_slot(self):
        response = slot(jid='admin@example.com', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        upload = Upload.objects.first()
        self.assertEqual(upload.jid, 'admin@example.com')
        self.assertEqual(upload.name, 'example.jpg')
        self.assertEqual(upload.size, 10)
        self.assertIsNone(upload.type)
        self.assertIsNotNone(upload.hash)

    def test_normalized_filename(self):
        response = slot(jid='admin@example.com', name='ex/ample.jpg', size=10)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        upload = Upload.objects.first()
        self.assertEqual(upload.jid, 'admin@example.com')
        self.assertEqual(upload.name, 'example.jpg')
        self.assertEqual(upload.size, 10)
        self.assertIsNone(upload.type)
        self.assertIsNotNone(upload.hash)

    def test_blocked(self):
        response = slot(jid='blocked@jabber.at', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 0)

    def test_max_file_size(self):
        response = slot(jid=user_jid, name='example.jpg', size=1024 * 1024)
        self.assertEquals(response.status_code, 413)
        self.assertEquals(Upload.objects.count(), 0)

        size = 300 * 1024
        response = slot(jid=user_jid, name='example.jpg', size=size)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        upload = Upload.objects.first()
        self.assertEqual(upload.jid, user_jid)
        self.assertEqual(upload.name, 'example.jpg')
        self.assertEqual(upload.size, size)
        self.assertIsNone(upload.type)
        self.assertIsNotNone(upload.hash)

    def test_max_total_size(self):
        # first, create some uploads manually so we're almost at the limit
        for i in range(1, 11):
            Upload.objects.create(jid=user_jid, name='example%s.jpg' % i, size=300 * 1024)

        # created is auto_now, and we cannot override it, but we can update it
        Upload.objects.update(created=timezone.now() - timedelta(hours=2))

        # now we would be over quota
        response = slot(jid=user_jid, name='example%s.jpg' % i, size=300 * 1024)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 10)

    def test_bytes_per_timedelta(self):
        # First, upload two files totalling 800 KB
        for i in range(1, 3):
            response = slot(jid=user_jid, name='example%s.jpg' % i, size=400 * 1024)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(Upload.objects.count(), i)
        self.assertEquals(Upload.objects.count(), i)

        # next slot would exceed bytes_per_timedelta, but not uploads_per_timedelta
        response = slot(jid=user_jid, name='example%s.jpg' % (i + 1), size=400 * 1024)
        self.assertEquals(response.status_code, 402)
        self.assertEquals(Upload.objects.count(), i)

    def test_uploads_per_timedelta(self):
        # first, create some uploads manually so we're almost at the limit
        for i in range(1, 4):
            response = slot(jid=user_jid, name='example%s.jpg' % i, size=10 * 1024)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(Upload.objects.count(), i)
        self.assertEquals(Upload.objects.count(), i)

        response = slot(jid=user_jid, name='example%s.jpg' % (i + 1), size=10 * 1024)
        self.assertEquals(response.status_code, 402)
        self.assertEquals(Upload.objects.count(), i)

    def test_mime_type(self):
        response = slot(jid='admin@example.com', name='example.jpg', size=10, type='foo/bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        upload = Upload.objects.first()
        self.assertEqual(upload.jid, 'admin@example.com')
        self.assertEqual(upload.name, 'example.jpg')
        self.assertEqual(upload.size, 10)
        self.assertEqual(upload.type, 'foo/bar')
        self.assertIsNotNone(upload.hash)

    def test_bad_requests(self):
        # jid missing
        response = slot(name='example.jpg', size=10)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

        # name missing
        response = slot(jid='admin@example.com', size=10)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

        # size missing
        response = slot(jid='admin@example.com', name='example.jpg')
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

        # malformed size
        response = slot(jid='admin@example.com', name='example.jpg', size='foo')
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

        # negative size
        response = slot(jid='admin@example.com', name='example.jpg', size=-3)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

    @override_settings(XMPP_HTTP_UPLOAD_ACCESS=[
        ('^admin@example\.com$', {}),
    ])
    def test_no_matching_acl(self):
        # This works:
        response = slot(jid='admin@example.com', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        # But this doesn't match any ACL, so we get forbidden
        response = slot(jid='admin@example.net', name='example.jpg', size=10)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Upload.objects.count(), 1)


@override_settings(XMPP_HTTP_UPLOAD_ACCESS=[
    ('^admin@example\.com$', {}),
    ('^user@example\.com$', {'max_file_size': 100, }),
])
class MaxSizeViewTest(TestCase):
    def req(self, *args, **kwargs):
        url = reverse('xmpp-http-upload:max_size')
        c = Client()
        return c.get(url, *args, **kwargs)

    def test_unrestricted(self):
        response = self.req({'jid': 'admin@example.com'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, b'0')

    def test_restricted(self):
        response = self.req({'jid': 'user@example.com'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, b'100')

    def test_non_matching(self):
        response = self.req({'jid': 'foo@example.com'})
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.content, b'You are not allowed to upload files.')

    def test_no_jid(self):
        response = self.req()
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, b'"jid" is a required GET parameter.')

    def test_json(self):
        response = self.req({'jid': 'user@example.com', 'output': 'application/json'})
        self.assertEquals(response.status_code, 200)

        # TODO: Use response.json() when Django 1.8 is no longer supported.
        self.assertEquals(json.loads(response.content.decode('utf-8')), {'max_size': 100})

    def test_unknown_content_type(self):
        response = self.req({'jid': 'user@example.com', 'output': 'application/foobar'})
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, b'Unsupported content type in output.')


class UploadTest(TestCase):
    def request_slot(self, filename, size, **kwargs):
        response = slot(jid=user_jid, name=filename, size=size, **kwargs)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)
        return response.content.decode('utf-8').split()

    def assertUpload(self, filename, content):
        # First request a slot
        self.assertEquals(Upload.objects.count(), 0)
        put_url, get_url = self.request_slot(filename, size=len(content))

        # Upload the file
        put_path = urlsplit(put_url).path
        response = put(put_path, content)
        self.assertEquals(response.status_code, 201)

        # Get the object, verify that the same URLs are generated
        upload = Upload.objects.all()[0]  # we verified there is exactly one above
        try:
            self.assertEqual((put_url, get_url), upload.get_urls(response.wsgi_request))

            # open the file, verify contents
            self.assertEqual(six.b(content), upload.file.read())

            # try to download it
            self.assertEqual(upload.file.url, urlsplit(get_url).path)
        finally:
            # remove file
            upload.file.delete(save=True)

    def test_basic(self):
        self.assertUpload('example.txt', 'this is a test')

    def test_space(self):
        self.assertUpload('example new.txt', 'this is a test')

    def test_umlaut(self):
        self.assertUpload('exämple.txt', 'this is a test')

    def test_unicode(self):
        self.assertUpload('صباح الخير يا صاحب.txt', 'testcontent')

    def test_non_existing(self):
        filename = 'example.jpg'
        content = 'foobar'
        put_url, get_url = self.request_slot(filename, size=len(content), type='text/plain')
        upload = Upload.objects.first()
        self.assertEqual(upload.file.name, '')
        self.assertEqual(upload.type, 'text/plain')

        false_put_url = reverse('xmpp-http-upload:share', kwargs={'hash': 'f' * 32, 'filename': filename})
        put_path = urlsplit(false_put_url).path
        response = put(put_path, content)
        self.assertEquals(response.status_code, 403)
        upload = Upload.objects.get(pk=upload.pk)
        self.assertEqual(upload.file.name, '')
        self.assertEqual(response.content, b'')

        put_path = urlsplit(put_url).path
        response = put(put_path, content + 'foobar')
        self.assertEquals(response.status_code, 400)
        upload = Upload.objects.get(pk=upload.pk)
        self.assertEqual(upload.file.name, '')
        self.assertEqual(response.content, b'File size (12) does not match requested size (6).')

        put_path = urlsplit(put_url).path
        response = put(put_path, content)
        self.assertEquals(response.status_code, 400)
        upload = Upload.objects.get(pk=upload.pk)
        self.assertEqual(upload.file.name, '')
        self.assertEqual(response.content,
                         b'Content type (application/octet-stream) does not match requested type.')

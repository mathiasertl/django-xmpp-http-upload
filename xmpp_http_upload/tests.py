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

import os
from datetime import timedelta
from http import HTTPStatus
from urllib.parse import urlsplit

from freezegun import freeze_time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import Upload
from .tasks import cleanup_http_uploads
from .utils import ws_download

user_jid = 'example@example.net'


def slot(**kwargs):
    url = reverse('xmpp-http-upload:slot')
    c = Client()
    return c.get(url, kwargs)


def get(path, **kwargs):
    c = Client()
    return c.get(path, **kwargs)


def put(path, data, content_type='application/octet-stream', **kwargs):
    c = Client()
    return c.put(path, data, content_type=content_type)


class UploadModelTestCase(TestCase):
    def setUp(self):
        self.content = 'example content'
        self.jid = 'user@example.com'
        self.name = 'example.txt'
        self.size = len(self.content)
        self.type = 'text/plain'
        self.hash = get_random_string(32)

        self.upload = Upload.objects.create(
            jid=self.jid, name=self.name, size=self.size, type=self.type, hash=self.hash
        )

    def test_get_absolute_url(self):
        self.assertEqual(self.upload.get_absolute_url(),
                         '/http_upload/share/%s/%s' % (self.hash, self.name))

    def test_get_urls(self):
        factory = RequestFactory()
        request = factory.get(self.upload.get_absolute_url())

        with self.settings(XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD=False):
            put_url, get_url = self.upload.get_urls(request)
            self.assertEqual(put_url, request.build_absolute_uri(self.upload.get_absolute_url()))
            self.assertEqual(get_url, request.build_absolute_uri(self.upload.get_absolute_url()))

        with self.settings(XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD=True):
            self.upload.file.save(self.name, ContentFile(self.content))

            put_url, get_url = self.upload.get_urls(request)
            self.assertEqual(put_url, request.build_absolute_uri(self.upload.get_absolute_url()))
            self.assertEqual(get_url, request.build_absolute_uri(self.upload.file.url))

        with self.settings(XMPP_HTTP_UPLOAD_URL_BASE='https://example.com'):
            put_url, get_url = self.upload.get_urls(request)
            put_exp = settings.XMPP_HTTP_UPLOAD_URL_BASE + self.upload.get_absolute_url()
            get_exp = settings.XMPP_HTTP_UPLOAD_URL_BASE + self.upload.file.url
            self.assertEqual(put_url, put_exp)
            self.assertEqual(get_url, get_exp)

        with self.settings(XMPP_HTTP_UPLOAD_URL_BASE='https://example.com/',
                           MEDIA_URL='https://example.net/'):
            put_url, get_url = self.upload.get_urls(request)
            put_exp = settings.XMPP_HTTP_UPLOAD_URL_BASE + self.upload.get_absolute_url()
            self.assertEqual(put_url, put_exp)
            self.assertEqual(get_url, self.upload.file.url)  # if MEDIA_URL is set, file.url is complete URL

        with self.settings(XMPP_HTTP_UPLOAD_URL_BASE='http://example.com/',
                           MEDIA_URL='http://example.net/',
                           XMPP_HTTP_UPLOAD_URL_HTTPS=True):
            put_url, get_url = self.upload.get_urls(request)
            put_exp = settings.XMPP_HTTP_UPLOAD_URL_BASE + self.upload.get_absolute_url()
            self.assertEqual(put_url, put_exp.replace('http://', 'https://'))
            self.assertEqual(get_url, self.upload.file.url.replace('http://', 'https://'))


class AdminChangelistViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='u', password='p', email='user@example.com')
        self.changelist_url = reverse('admin:xmpp_http_upload_upload_changelist')
        self.client = Client()
        self.client.force_login(self.user)

        self.content = 'example content'
        self.jid = 'user@example.com'
        self.name1 = 'example.txt'
        self.name2 = 'example.jpg'
        self.size = len(self.content)
        self.type = 'text/plain'
        self.hash = get_random_string(32)

        self.u1 = Upload.objects.create(
            jid=self.jid, name=self.name1, size=self.size, type=self.type, hash=self.hash
        )
        self.u2 = Upload.objects.create(
            jid=self.jid, name=self.name2, size=self.size, type=self.type, hash=self.hash
        )

    def assertResponse(self, response, *uploads):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['cl'].result_list), set(uploads))

    def test_get(self):
        response = self.client.get(self.changelist_url)
        self.assertResponse(response, self.u1, self.u2)

    def test_not_uploaded(self):
        response = self.client.get(self.changelist_url, {'uploaded': '0'})
        self.assertResponse(response, self.u1, self.u2)

        # upload u1 and test we only get u2
        self.u1.file.save(self.name1, ContentFile(self.content))
        response = self.client.get(self.changelist_url, {'uploaded': '0'})
        self.assertResponse(response, self.u2)

    def test_uploaded(self):
        response = self.client.get(self.changelist_url, {'uploaded': '1'})
        self.assertResponse(response)

        # upload u1 and test we get u1
        self.u1.file.save(self.name1, ContentFile(self.content))
        response = self.client.get(self.changelist_url, {'uploaded': '1'})
        self.assertResponse(response, self.u1)

    def test_expired(self):
        with freeze_time(timezone.now()) as frozen:
            response = self.client.get(self.changelist_url, {'uploaded': '2'})
            self.assertResponse(response)

            frozen.tick(delta=timedelta(seconds=361))  # XMPP_HTTP_UPLOAD_PUT_TIMEOUT + 1
            response = self.client.get(self.changelist_url, {'uploaded': '2'})
            self.assertResponse(response, self.u1, self.u2)  # they're all expired


class RequestSlotTestCase(TestCase):
    def assertSlot(self, jid='admin@example.com', filename='example.jpg', size=10,
                   expected_filename=None,
                   **kwargs):
        expected_filename = expected_filename or filename
        response = slot(jid=jid, name=filename, size=size, **kwargs)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        upload = Upload.objects.first()
        self.assertEqual(upload.jid, jid)
        self.assertEqual(upload.name, expected_filename)
        self.assertEqual(upload.size, size)
        self.assertIsNone(upload.type)
        self.assertIsNotNone(upload.hash)
        return response, upload

    def assertNoSlot(self, status_code, message, jid='admin@example.com'):
        response = slot(jid=jid, name='example.jpg', size=10)
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response.content, message)
        self.assertEquals(Upload.objects.count(), 0)

    def test_slot(self):
        self.assertSlot()

    def test_normalized_filename(self):
        self.assertSlot(filename='ex/ample.jpg', expected_filename='example.jpg')

    def test_blocked(self):
        self.assertNoSlot(403, b'You are not allowed to upload files.', jid='blocked@jabber.at')

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

    def test_json(self):
        response = slot(jid='admin@example.com', name='example.jpg', size=10, output='application/json')
        upload = Upload.objects.first()
        put_url, get_url = upload.get_urls(response.wsgi_request)

        self.assertEquals(response.json(), {
            'get': get_url,
            'put': put_url,
        })
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Upload.objects.count(), 1)

        self.assertEqual(upload.jid, 'admin@example.com')
        self.assertEqual(upload.name, 'example.jpg')
        self.assertEqual(upload.size, 10)
        self.assertIsNone(upload.type)
        self.assertIsNotNone(upload.hash)

    def test_no_content_length(self):
        # TODO: There seems to be no difference in the response at this level. Maybe the webserver adds it?

        with self.settings(XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH=False):
            response, upload = self.assertSlot()

    def test_add_content_length(self):
        # TODO: There seems to be no difference in the response at this level. Maybe the webserver adds it?

        with self.settings(XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH=True):
            response, upload = self.assertSlot()

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

        # filename to long
        response = slot(jid='admin@example.com', name='a' * 255, size=10)
        self.assertEquals(response.status_code, 413)
        self.assertEquals(Upload.objects.count(), 0)

        # invalid content type
        response = slot(jid='admin@example.com', name='example.jpg', size=10, output='foo/bar')
        self.assertEquals(response.content, b"Unsupported content type in output.")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(Upload.objects.count(), 0)

    @override_settings(XMPP_HTTP_UPLOAD_ACCESS=[
        (r'^admin@example\.com$', {}),
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
    (r'^admin@example\.com$', {}),
    (r'^user@example\.com$', {'max_file_size': 100, }),
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

        self.assertEquals(response.json(), {'max_size': 100})

    def test_no_content_length(self):
        # TODO: There seems to be no difference in the response at this level. Maybe the webserver adds it?

        with self.settings(XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH=False):
            response = self.req({'jid': 'admin@example.com'})
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content, b'0')

    def test_add_content_length(self):
        # TODO: There seems to be no difference in the response at this level. Maybe the webserver adds it?

        with self.settings(XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH=True):
            response = self.req({'jid': 'admin@example.com'})
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content, b'0')

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

    def assertUpload(self, filename, content, delete=True, content_type=None):
        # First request a slot
        self.assertEquals(Upload.objects.count(), 0)
        slot_kwargs = {}
        if content_type:
            slot_kwargs['type'] = content_type
        put_url, get_url = self.request_slot(filename, size=len(content), **slot_kwargs)

        # Upload the file
        put_path = urlsplit(put_url).path
        put_kwargs = {}
        if content_type:
            put_kwargs['content_type'] = content_type
        response = put(put_path, content, **put_kwargs)
        self.assertEquals(response.status_code, 201)

        # Get the object, verify that the same URLs are generated
        upload = Upload.objects.all()[0]  # we verified there is exactly one above
        try:
            self.assertEqual((put_url, get_url), upload.get_urls(response.wsgi_request))

            # open the file, verify contents
            self.assertEqual(bytes(content, 'utf-8'), upload.file.read())

            # Test the file url, but ownly if webserver download is configured
            if ws_download() is True:
                self.assertEqual(upload.file.url, urlsplit(get_url).path)
        finally:
            if delete is True:  # remove file
                upload.file.delete(save=True)
        return upload, put_url, get_url

    def test_basic(self):
        self.assertUpload('example.txt', 'this is a test')

    def test_space(self):
        self.assertUpload('example new.txt', 'this is a test')

    def test_umlaut(self):
        self.assertUpload('exämple.txt', 'this is a test')

    def test_unicode(self):
        self.assertUpload('صباح الخير يا صاحب.txt', 'testcontent')

    def test_direct_download(self):
        # test that we can download a file
        filename = 'example.txt'
        content = 'this is a test'

        try:
            with self.settings(XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD=False):
                upload, put_url, get_url = self.assertUpload(filename, content, delete=False)
                response = get(urlsplit(get_url).path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), bytes(content, 'utf-8'))
                self.assertEqual(response['Content-Type'], 'application/octet-stream')
                self.assertEqual(response['Content-Length'], str(len(content)))
                self.assertEqual(response.filename, filename)
        finally:
            upload.file.delete(save=True)

    def test_direct_download_content_type(self):
        # test that we can download a file
        filename = 'example.txt'
        content = 'this is a test'
        ct = 'text/plain'

        try:
            with self.settings(XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD=False):
                upload, put_url, get_url = self.assertUpload(filename, content, delete=False,
                                                             content_type=ct)
                response = get(urlsplit(get_url).path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), bytes(content, 'utf-8'))
                self.assertEqual(response['Content-Type'], ct)
                self.assertEqual(response['Content-Length'], str(len(content)))
                self.assertEqual(response.filename, filename)
        finally:
            upload.file.delete(save=True)

    def test_webserver_download(self):
        filename = 'example.txt'
        content = 'foo'

        with self.settings(XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD=True):
            upload, put_url, get_url = self.assertUpload(filename, content, delete=False)
            self.assertEqual(urlsplit(get_url).path, upload.file.url)

            # NOTE: put_url is the same as the direct download path
            response = get(urlsplit(put_url).path)
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

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


class CleanupMixin:
    def setUp(self):
        self.content = 'example content'
        self.jid = 'user@example.com'
        self.name1 = 'example.txt'
        self.name2 = 'example.jpg'
        self.size = len(self.content)
        self.type = 'text/plain'
        self.hash = get_random_string(32)

        self.u1 = Upload.objects.create(
            jid=self.jid, name=self.name1, size=self.size, type=self.type, hash=self.hash
        )
        self.u2 = Upload.objects.create(
            jid=self.jid, name=self.name2, size=self.size, type=self.type, hash=self.hash
        )

    @property
    def slots_expired(self):
        return timezone.now() + timedelta(seconds=361)

    @property
    def files_expired(self):
        return timezone.now() + timedelta(seconds=86400 * 32)

    def test_basic(self):
        # first, nothing happens...
        self.cleanup()
        u1 = Upload.objects.get(pk=self.u1.pk)
        u2 = Upload.objects.get(pk=self.u2.pk)
        self.assertFalse(u1.file)
        self.assertFalse(u2.file)

        # save a file, and still nothing happens
        self.u1.file.save(self.name1, ContentFile(self.content))
        self.cleanup()
        u1 = Upload.objects.get(pk=self.u1.pk)
        u2 = Upload.objects.get(pk=self.u2.pk)
        self.assertTrue(os.path.exists(u1.file.path))
        self.assertFalse(u2.file)

    def test_expired_slots(self):
        self.u1.file.save(self.name1, ContentFile(self.content))

        # cleanup slots that have no file uploaded
        with freeze_time(self.slots_expired):
            # cleanup with no empty slot removal - nothing should be removed
            self.cleanup(slots=False)
            self.assertTrue(Upload.objects.filter(pk=self.u1.pk).exists())
            self.assertTrue(Upload.objects.filter(pk=self.u2.pk).exists())

            self.cleanup()
            self.assertTrue(Upload.objects.filter(pk=self.u1.pk).exists())
            self.assertFalse(Upload.objects.filter(pk=self.u2.pk).exists())

    def test_files_expired(self):
        self.u1.file.save(self.name1, ContentFile(self.content))
        self.u2.file.save(self.name2, ContentFile(self.content))

        with freeze_time(self.files_expired):
            self.cleanup(files=False)
            self.assertTrue(Upload.objects.filter(pk=self.u1.pk).exists())
            self.assertTrue(Upload.objects.filter(pk=self.u2.pk).exists())
            self.assertTrue(os.path.exists(self.u1.file.path))
            self.assertTrue(os.path.exists(self.u2.file.path))

            self.cleanup(timeout=86400 * 64)
            self.assertTrue(Upload.objects.filter(pk=self.u1.pk).exists())
            self.assertTrue(Upload.objects.filter(pk=self.u2.pk).exists())
            self.assertTrue(os.path.exists(self.u1.file.path))
            self.assertTrue(os.path.exists(self.u2.file.path))

            self.cleanup()
            self.assertFalse(Upload.objects.filter(pk=self.u1.pk).exists())
            self.assertFalse(Upload.objects.filter(pk=self.u2.pk).exists())
            self.assertFalse(os.path.exists(self.u1.file.path))
            self.assertFalse(os.path.exists(self.u2.file.path))


class CeleryCleanupTaskTestCase(CleanupMixin, TestCase):
    def cleanup(self, **kwargs):
        cleanup_http_uploads(**kwargs)


class ManageCleanupCommandTestCase(CleanupMixin, TestCase):
    def cleanup(self, slots=True, files=True, timeout=None):
        kwargs = {}
        if not slots:
            kwargs['no_slots'] = False
        if not files:
            kwargs['no_files'] = False
        if timeout:
            kwargs['timeout'] = int(timeout / 86400)

        call_command('cleanup_http_uploads', **kwargs)

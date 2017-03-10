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

from django.core.management.base import BaseCommand

from xmpp_http_upload.models import Upload


class Command(BaseCommand):
    help = 'Cleanup old uploaded files'

    def add_arguments(self, parser):
        parser.add_argument(
            'timeout', nargs='?', type=int, default=None,
            help='Minimum age of files to delete in days. Defaults to the '
                 'XMPP_HTTP_UPLOAD_SHARE_TIMEOUT setting.'
        )
        parser.add_argument(
            '-s', '--no-slots', default=True, dest='slots', action='store_false',
            help='Do not cleanup expired slots.')
        parser.add_argument(
            '-f', '--no-files', default=True, dest='files', action='store_false',
            help='Do not cleanup expired files.')

    def handle(self, *args, **options):
        slots = options['slots']
        files = options['files']
        timeout = None
        if options['timeout'] is not None:
            timeout = options['timeout'] * 86400
        Upload.objects.cleanup(slots=slots, files=files, timeout=timeout)

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

import re

from django.conf import settings


def ws_download():
    return getattr(settings, 'XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD', True)


def get_config(jid):
    """Get the configuration for the given JID based on XMPP_HTTP_UPLOAD_ACCESS.

    If the JID does not match any rule, ``False`` is returned.
    """

    acls = getattr(settings, 'XMPP_HTTP_UPLOAD_ACCESS', (('.*', False), ))

    for regex, config in acls:
        if isinstance(regex, str):
            regex = [regex]

        for subex in regex:
            if re.search(subex, jid):
                return config

    return False

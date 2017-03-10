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

from django.conf.urls import url

from . import views

app_name = 'xmpp-http-upload'
urlpatterns = [
    url(r'^slot/$', views.RequestSlotView.as_view(), name='slot'),
    url(r'^max_size/$', views.MaxSizeView.as_view(), name='max_size'),

    # TODO: The filename regex should exclude unsafe characters
    url(r'^share/(?P<hash>[a-zA-Z0-9]{32})/(?P<filename>.*)$', views.UploadView.as_view(),
        name='share'),
]

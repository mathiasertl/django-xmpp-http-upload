# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import xmpp_http_upload.models


class Migration(migrations.Migration):

    dependencies = [
        ('xmpp_http_upload', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='file',
            field=models.FileField(max_length=255, null=True, upload_to=xmpp_http_upload.models.get_upload_path, blank=True),
        ),
    ]

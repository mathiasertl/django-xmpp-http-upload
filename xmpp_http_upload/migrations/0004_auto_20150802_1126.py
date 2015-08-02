# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import xmpp_http_upload.models


class Migration(migrations.Migration):

    dependencies = [
        ('xmpp_http_upload', '0003_upload_jid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='file',
            field=models.FileField(null=True, upload_to=xmpp_http_upload.models.get_upload_path, blank=True),
        ),
    ]

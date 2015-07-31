# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('xmpp_http_upload', '0002_upload_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='jid',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]

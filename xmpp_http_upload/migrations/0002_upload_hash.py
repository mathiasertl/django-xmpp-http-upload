# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('xmpp_http_upload', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='hash',
            field=models.CharField(default='none', max_length=64),
            preserve_default=False,
        ),
    ]

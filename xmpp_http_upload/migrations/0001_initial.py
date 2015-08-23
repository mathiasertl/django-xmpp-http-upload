# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import xmpp_http_upload.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('jid', models.CharField(max_length=256)),
                ('name', models.CharField(max_length=256)),
                ('size', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=64, null=True, blank=True)),
                ('hash', models.CharField(max_length=64)),
                ('file', models.FileField(null=True, upload_to=xmpp_http_upload.models.get_upload_path, blank=True)),
                ('uploaded', models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]

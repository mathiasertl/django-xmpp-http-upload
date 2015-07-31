# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


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
                ('name', models.CharField(max_length=256)),
                ('size', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=64, null=True, blank=True)),
                ('file', models.FileField(null=True, upload_to=b'http_upload', blank=True)),
                ('uploaded', models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]

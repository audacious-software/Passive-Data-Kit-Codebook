# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-05-05 13:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit_codebook', '0006_auto_20230505_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='datapointtype',
            name='category',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]

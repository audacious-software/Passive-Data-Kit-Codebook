# pylint: skip-file
# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-05-05 13:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit_codebook', '0005_datapointtype_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='datapointtype',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='datapointtype',
            name='name',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]

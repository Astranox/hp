# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-16 11:20
from __future__ import unicode_literals

import account.models
from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_auto_20161014_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlogentry',
            name='payload',
            field=jsonfield.fields.JSONField(default=account.models.default_payload),
        ),
    ]

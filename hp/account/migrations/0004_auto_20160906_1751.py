# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-06 17:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_confirmation_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmation',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='confirmations', to='core.Address'),
        ),
    ]

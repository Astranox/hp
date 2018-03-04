# Generated by Django 2.0.2 on 2018-03-04 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certs', '0003_auto_20180101_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='enabled',
            field=models.BooleanField(default=True, help_text='Disabled certificates are not displayed anywhere.'),
        ),
    ]
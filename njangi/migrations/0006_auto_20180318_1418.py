# Generated by Django 2.0 on 2018-03-18 14:18

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0005_auto_20180318_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='related_users',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='related users'),
        ),
    ]

# Generated by Django 2.0 on 2018-03-18 14:17

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0004_auto_20180318_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='amount'),
        ),
        migrations.AlterField(
            model_name='useraccount',
            name='related_users',
            field=django.contrib.postgres.fields.jsonb.JSONField(verbose_name='related users'),
        ),
    ]

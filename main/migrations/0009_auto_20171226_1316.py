# Generated by Django 2.0 on 2017-12-26 13:16

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20171219_2129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='tel1',
            field=phonenumber_field.modelfields.PhoneNumberField(help_text='*', max_length=128, verbose_name='MTN number'),
        ),
    ]

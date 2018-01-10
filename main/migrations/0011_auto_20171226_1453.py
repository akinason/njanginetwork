# Generated by Django 2.0 on 2017-12-26 14:53

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20171226_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='tel2',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='*', max_length=128, null=True, verbose_name='MTN number'),
        ),
        migrations.AlterField(
            model_name='user',
            name='tel3',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='*', max_length=128, null=True, verbose_name='MTN number'),
        ),
    ]
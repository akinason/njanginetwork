# Generated by Django 2.0 on 2018-01-11 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_auto_20180111_2013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='allow_automatic_contribution',
            field=models.BooleanField(default=False, verbose_name='allow automatic contributions'),
        ),
    ]
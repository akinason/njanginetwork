# Generated by Django 2.0 on 2018-03-26 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0011_accountpackage_is_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountpackage',
            name='rank',
            field=models.IntegerField(default=0, verbose_name='rank'),
        ),
    ]
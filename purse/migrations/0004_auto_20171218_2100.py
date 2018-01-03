# Generated by Django 2.0 on 2017-12-18 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0003_walletmodel_thirdparty_reference'),
    ]

    operations = [
        migrations.AddField(
            model_name='walletmodel',
            name='nsp',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='network service provider'),
        ),
        migrations.AddField(
            model_name='walletmodel',
            name='tel',
            field=models.CharField(blank=True, max_length=9, verbose_name='phone number'),
        ),
        migrations.AlterField(
            model_name='walletmodel',
            name='thirdparty_reference',
            field=models.CharField(db_index=True, max_length=30, verbose_name='third party reference'),
        ),
    ]

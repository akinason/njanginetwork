# Generated by Django 2.0 on 2017-12-18 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0002_walletmodel_charge'),
    ]

    operations = [
        migrations.AddField(
            model_name='walletmodel',
            name='thirdparty_reference',
            field=models.CharField(default=0, max_length=30, verbose_name='third party reference'),
            preserve_default=False,
        ),
    ]
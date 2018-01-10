# Generated by Django 2.0 on 2017-12-18 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0006_auto_20171218_2134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='walletmodel',
            name='reference',
            field=models.CharField(db_index=True, max_length=20, null=True, unique=True, verbose_name='reference'),
        ),
        migrations.AlterField(
            model_name='walletmodel',
            name='trans_code',
            field=models.CharField(blank=True, max_length=20, verbose_name='transaction code'),
        ),
    ]
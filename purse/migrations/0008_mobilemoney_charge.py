# Generated by Django 2.0 on 2018-02-25 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0007_mobilemoney_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilemoney',
            name='charge',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='charge'),
        ),
    ]

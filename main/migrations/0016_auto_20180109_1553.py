# Generated by Django 2.0 on 2018-01-09 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_levelmodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='levelmodel',
            name='upgrade_after',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='upgrade after'),
        ),
    ]
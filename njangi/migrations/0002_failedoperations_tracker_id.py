# Generated by Django 2.0 on 2018-02-27 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='failedoperations',
            name='tracker_id',
            field=models.CharField(blank=True, max_length=15, verbose_name='tracker id'),
        ),
    ]

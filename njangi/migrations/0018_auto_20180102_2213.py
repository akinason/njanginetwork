# Generated by Django 2.0 on 2018-01-02 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0017_auto_20171229_0833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='failedoperations',
            name='operation_type',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='failedoperations',
            name='response_status',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='failedoperations',
            name='status',
            field=models.CharField(max_length=50),
        ),
    ]
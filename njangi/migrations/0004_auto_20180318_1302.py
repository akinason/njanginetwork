# Generated by Django 2.0 on 2018-03-18 13:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0003_accountpackage_useraccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='created_on',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='created on'),
        ),
        migrations.AlterField(
            model_name='useraccount',
            name='related_users',
            field=models.CharField(blank=True, max_length=255, verbose_name='related users'),
        ),
    ]
# Generated by Django 2.0 on 2018-05-04 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_contributed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_in_network',
            field=models.BooleanField(default=False),
        ),
    ]
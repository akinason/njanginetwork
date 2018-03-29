# Generated by Django 2.0 on 2018-03-27 01:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_user_user_account_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=255, verbose_name='notification type')),
                ('text', models.CharField(max_length=255, verbose_name='notification')),
                ('link', models.CharField(blank=True, max_length=255, verbose_name='notification link')),
                ('is_read', models.BooleanField(default=False, verbose_name='is read')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date')),
                ('read_on', models.DateTimeField(blank=True, null=True, verbose_name='read on')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

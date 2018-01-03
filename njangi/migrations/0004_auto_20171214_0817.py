# Generated by Django 2.0 on 2017-12-14 08:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0003_auto_20171214_0814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='njangitree',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='child_user', to=settings.AUTH_USER_MODEL, verbose_name='child user'),
        ),
    ]

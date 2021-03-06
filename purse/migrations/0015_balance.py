# Generated by Django 2.0 on 2019-07-23 13:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('purse', '0014_auto_20180901_2016'),
    ]

    operations = [
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available_balance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='available balance')),
                ('upgrade_balance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='upgrade balance')),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='balance', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
    ]

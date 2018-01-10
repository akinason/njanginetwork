# Generated by Django 2.0 on 2017-12-12 20:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('njangi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LevelTree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveIntegerField(verbose_name='user level')),
                ('is_active', models.BooleanField(default=True)),
                ('last_payment', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last payment date')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('total_sent', models.DecimalField(decimal_places=2, max_digits=20)),
                ('total_received', models.DecimalField(decimal_places=2, max_digits=20)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='last_recipient', to=settings.AUTH_USER_MODEL, verbose_name='recipient')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='level_user', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveIntegerField(verbose_name='level')),
                ('sender_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('processing_fee', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('recipient_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('sender_status', models.CharField(choices=[('pending_confirmation', 'pending confirmation'), ('completed', 'completed'), ('cancelled', 'cancelled')], max_length=20, verbose_name='sender status')),
                ('sender_tel', models.CharField(blank=True, max_length=15, verbose_name='sender mobile')),
                ('sender_nsp', models.CharField(choices=[('mtn', 'MTN'), ('orange', 'Orange')], max_length=10)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, verbose_name='sent on')),
                ('recipient_status', models.CharField(choices=[('provide_contact', 'provide contact'), ('completed', 'completed'), ('processing', 'processing'), ('cancelled', 'cancelled')], max_length=20, verbose_name='recipient status')),
                ('recipient_tel', models.CharField(blank=True, max_length=15, verbose_name='sender mobile')),
                ('status', models.CharField(choices=[('processing', 'processing'), ('cancelled', 'cancelled'), ('completed', 'completed')], max_length=20, verbose_name='status')),
                ('completed_on', models.DateTimeField(blank=True, null=True, verbose_name='completed_on')),
                ('attempts', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='attempts')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipient', to=settings.AUTH_USER_MODEL, verbose_name='recipient')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender', to=settings.AUTH_USER_MODEL, verbose_name='sender')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='leveltree',
            unique_together={('user', 'level')},
        ),
    ]
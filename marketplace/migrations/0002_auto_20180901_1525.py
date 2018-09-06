# Generated by Django 2.0 on 2018-09-01 15:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='paid_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoice',
            name='paid_on',
            field=models.DateTimeField(blank=True, null=True, verbose_name='paid on'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payment_method',
            field=models.CharField(blank=True, max_length=255, verbose_name='payment method'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_owner', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='discount',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=10, verbose_name='discount'),
        ),
    ]
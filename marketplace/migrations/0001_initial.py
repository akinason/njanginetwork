# Generated by Django 2.0 on 2018-09-01 12:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Commission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField()),
                ('percentage', models.DecimalField(decimal_places=3, max_digits=3)),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.DecimalField(decimal_places=3, default=0.0, max_digits=10, verbose_name='invoice total')),
                ('status', models.CharField(choices=[('DRAFT', 'DRAFT'), ('PENDING_PAYMENT', 'PENDING_PAYMENT'), ('PAID', 'PAID'), ('CANCELLED', 'CANCELLED')], default='DRAFT', max_length=255, verbose_name='status')),
                ('is_paid', models.BooleanField(default=False)),
                ('payment_reference', models.CharField(blank=True, max_length=255, verbose_name='payment reference')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_owner', to=settings.AUTH_USER_MODEL, verbose_name='invoice')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=3, default=1, max_digits=10, verbose_name='quantity')),
                ('price', models.DecimalField(decimal_places=3, max_digits=10, verbose_name='price')),
                ('discount', models.DecimalField(decimal_places=3, max_digits=10, verbose_name='discount')),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10, verbose_name='amount')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketplace.Invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='product name')),
                ('code', models.CharField(blank=True, max_length=255, verbose_name='product code')),
                ('description', models.TextField(verbose_name='description')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='price')),
                ('company_commission', models.DecimalField(decimal_places=3, max_digits=3, verbose_name='company commission')),
                ('rating', models.IntegerField(blank=True, null=True, verbose_name='rating')),
                ('level_1_commission', models.DecimalField(decimal_places=3, default=30, max_digits=3, verbose_name='level 1 commission')),
                ('level_2_commission', models.DecimalField(decimal_places=3, default=15, max_digits=3, verbose_name='level 2 commission')),
                ('level_3_commission', models.DecimalField(decimal_places=3, default=5, max_digits=3, verbose_name='level 3 commission')),
                ('level_4_commission', models.DecimalField(decimal_places=3, default=0.0, max_digits=3, verbose_name='level 4 commission')),
                ('level_5_commission', models.DecimalField(decimal_places=3, default=0.0, max_digits=3, verbose_name='level 5 commission')),
                ('level_6_commission', models.DecimalField(decimal_places=3, default=0.0, max_digits=3, verbose_name='level 6 commission')),
                ('is_active', models.BooleanField(default=False)),
                ('auto_add_to_invoice', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_type', to='marketplace.ProductType', verbose_name='product type'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_product_item', to='marketplace.Product', verbose_name='product'),
        ),
        migrations.AddField(
            model_name='commission',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketplace.Invoice'),
        ),
        migrations.AddField(
            model_name='commission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

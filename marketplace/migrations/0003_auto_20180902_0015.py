# Generated by Django 2.0 on 2018-09-02 00:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0002_auto_20180901_1525'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='marketplace/product/', verbose_name='image')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketplace.Product')),
            ],
        ),
        migrations.AddField(
            model_name='invoice',
            name='is_commission_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='producttype',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='marketplace/product_type/', verbose_name='product type image'),
        ),
    ]

# Generated by Django 2.0 on 2018-09-02 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_auto_20180902_0015'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='background_image',
            field=models.ImageField(blank=True, null=True, upload_to='marketplace/product/'),
        ),
    ]
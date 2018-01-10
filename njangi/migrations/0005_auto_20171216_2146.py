# Generated by Django 2.0 on 2017-12-16 21:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('njangi', '0004_auto_20171214_0817'),
    ]

    operations = [
        migrations.CreateModel(
            name='NjangiLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.PositiveIntegerField(unique=True, verbose_name='njangi level')),
                ('contribution', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='contribution')),
            ],
        ),
        migrations.AlterField(
            model_name='leveltree',
            name='level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='njangi.NjangiLevel', verbose_name='user level'),
        ),
    ]
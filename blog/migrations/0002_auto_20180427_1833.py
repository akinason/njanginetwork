# Generated by Django 2.0 on 2018-04-27 18:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('body', tinymce.models.HTMLField(verbose_name='news content')),
                ('image', models.FileField(blank=True, upload_to='blog/category/sub/', verbose_name='image')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date created')),
                ('is_published', models.BooleanField(default=False)),
                ('view_count', models.IntegerField(verbose_name='view count')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Category')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
        migrations.RemoveField(
            model_name='news',
            name='user',
        ),
        migrations.DeleteModel(
            name='News',
        ),
    ]

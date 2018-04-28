from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from tinymce.models import HTMLField
# Create your models here.


class MainCategory(models.Model):
    name = models.CharField(_('category name'), max_length=255)
    image = models.FileField(_('image'), upload_to='blog/category/main/', blank=True)
    created_on = models.DateTimeField(_('date created'), default=timezone.now)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(_('category name'), max_length=255)
    main_category = models.ForeignKey(MainCategory, verbose_name=_('main category'), on_delete=models.CASCADE)
    image = models.FileField(_('image'), upload_to='blog/category/sub/', blank=True)
    created_on = models.DateTimeField(_('date created'), default=timezone.now)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Post(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(_('title'), max_length=255)
    body = HTMLField(_('news content'))
    user = models.ForeignKey(get_user_model(), verbose_name=_('user'), on_delete=models.SET_NULL, blank=True, null=True)
    image = models.FileField(_('image'), upload_to='blog/category/sub/', blank=True)
    created_on = models.DateTimeField(_('date created'), default=timezone.now)
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(_('view count'))

    def __str__(self):
        return self.title

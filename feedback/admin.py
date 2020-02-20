from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Feedback)
admin.site.register(models.Question)
admin.site.register(models.Response)
admin.site.register(models.QuestionOptionTable)

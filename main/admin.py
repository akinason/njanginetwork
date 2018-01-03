from django.contrib import admin
from django.contrib.auth import get_user_model

# Register your models here.
# class UserAdmin():

admin.site.register(
    get_user_model(),
    list_display=(
        'id', 'username', 'level', 'first_name', 'last_name', 'sponsor_id', 'sponsor', 'is_admin', 'tel1', 'tel2',
        'tel3', 'date_joined',
    )
)
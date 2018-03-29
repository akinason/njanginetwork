from django.contrib import admin
from django.contrib.auth import get_user_model

from main.models import LevelModel, Notification

# Register your models here.
# class UserAdmin():


class NotificationAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('notification_type', 'user__username', 'text')
    list_filter = ('type',)
    list_display = (
        'id', 'user', 'type', 'text', 'is_read', 'created_on', 'read_on', 'link'
    )

admin.site.register(Notification, NotificationAdmin)

admin.site.register(
    get_user_model(),
    list_display=(
        'id', 'username', 'level', 'first_name', 'last_name', 'email', 'sponsor_id', 'sponsor', 'is_admin', 'tel1', 'tel2',
        'tel3', 'date_joined',
    )
)

admin.site.register(
    LevelModel,
    list_display=(
        'id', 'level', 'cumm_downlines', 'contribution', 'receipts', 'cumm_receipts', 'cumm_contribution',
        'monthly_profit', 'upgrade_after'
    )
)


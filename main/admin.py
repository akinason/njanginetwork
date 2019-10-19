from django.contrib import admin
from django.contrib.auth import get_user_model

from main.models import LevelModel, Notification


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    model = get_user_model()
    search_fields = ('username', 'email', 'sponsor_id', 'sponsor', 'tel1')
    list_filter = ('sponsor', 'date_joined', 'level', 'id', 'sponsor_id')
    list_display = (
        'id', 'username', 'level', 'first_name', 'last_name', 'email', 'sponsor_id', 'network_parent', 'sponsor', 'is_admin', 'tel1',
        'tel2', 'tel3', 'date_joined',
    )


class NotificationAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('notification_type', 'user__username', 'text')
    list_filter = ('type', 'user__username')
    list_display = (
        'id', 'user', 'type', 'text', 'is_read', 'created_on', 'read_on', 'link'
    )


class LevelModelAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'level', 'cumm_downlines', 'contribution', 'receipts', 'cumm_receipts', 'cumm_contribution',
        'monthly_profit', 'upgrade_after'
    )


admin.site.register(Notification, NotificationAdmin)
admin.site.register(get_user_model(), UserAdmin)
admin.site.register(LevelModel, LevelModelAdmin)


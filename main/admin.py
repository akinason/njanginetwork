from django.contrib import admin
from django.contrib.auth import get_user_model
from main.models import LevelModel

# Register your models here.
# class UserAdmin():

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
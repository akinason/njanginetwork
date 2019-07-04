from django.contrib import admin

from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from njangi.models import (
    LevelModel, NjangiTree, FailedOperations, AccountPackage, UserAccount, RemunerationPlan
)

# Register your models here.

admin.site.register(
    NjangiTree,
    MPTTModelAdmin,
    list_display=(
        'id',
        'user',
        'parent_user',
        'side',
        'parent',
    ),
    list_display_links=(
            'user',
    ),
)


class LevelModelAdmin(admin.ModelAdmin):
    model = LevelModel
    search_fields = ('user__username', )
    list_filter = ('user', 'level', 'is_active', 'last_payment', 'user__username')
    list_display = ('user', 'level', 'is_active', 'last_payment', 'next_payment', 'total_sent', 'total_received')


admin.site.register(LevelModel, LevelModelAdmin)

admin.site.register(
    FailedOperations,
    list_display=(
        'id', 'user', 'recipient', 'level', 'amount', 'nsp', 'sender_tel', 'processing_fee',
        'transaction_id', 'status', 'operation_type', 'message', 'response_status',
        'created_on', 'resolved_on', 'attempts'
    )
)

admin.site.register(
    UserAccount,
    list_display=(
        'id', 'limit', 'related_users', 'account_manager', 'is_active', 'package', 'last_payment', 'next_payment'
    )
)

admin.site.register(
    AccountPackage,
    list_display=(
        'id', 'name', 'rank', 'limit','is_default', 'monthly_subscription', 'annual_subscription',
    )
)


class RemunerationPlanAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'level', 'contribution_amount', 'recipient_amount', 'company_commission', 'velocity_reserve',
        'direct_commission', 'network_commission'
    )


admin.site.register(RemunerationPlan, RemunerationPlanAdmin)

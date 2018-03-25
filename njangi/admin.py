from django.contrib import admin

from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from njangi.models import LevelModel, NjangiTree, FailedOperations, AccountPackage, UserAccount

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

admin.site.register(LevelModel,
                    list_display=('user', 'level', 'is_active', 'last_payment', 'next_payment',
                                  'total_sent', 'total_received')
                    )

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
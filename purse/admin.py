from django.contrib import admin
from .models import WalletModel, MobileMoney, Balance
# Register your models here.


class WalletModelAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'sender__username')
    list_filter = ('user__username', 'sender__username', 'trans_code', 'status', 'nsp',)
    list_display = (
        'id', 'description', 'information', 'amount', 'charge', 'user', 'sender', 'reference', 'trans_code', 'tel',
        'nsp',
        'status',
    )


class MobileMoneyAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('tel', 'tracker_id', 'user__username', 'uuid')
    list_filter = (
        'request_date', 'response_status', 'nsp', 'request_type', 'request_status', 'user__username',
        'is_complete'
        )
    list_display = (
        'id', 'tracker_id', 'request_type', 'request_status', 'response_code', 'response_status',
        'callback_status_code', 'is_complete', 'tel', 'nsp', 'amount', 'charge', 'request_date', 'invoice_number',
        'response_date', 'message', 'transaction_id', 'user', 'response_transaction_date',
        'user_auth', 'server_response', 'callback_server_response', 'provider', 'purpose', 'callback_response_date',
        'recipient', 'uuid',
    )


class BalanceAdmin(admin.ModelAdmin):
    model = Balance
    search_fields = ('user__username', )
    list_filter = ('last_updated', )
    list_display = ('user', 'available_balance', 'upgrade_balance', 'last_updated')


admin.site.register(MobileMoney, MobileMoneyAdmin)
admin.site.register(WalletModel, WalletModelAdmin)
admin.site.register(Balance, BalanceAdmin)

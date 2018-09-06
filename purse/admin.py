from django.contrib import admin
from .models import WalletModel, MobileMoney
# Register your models here.


class WalletModelAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'description', 'information', 'amount', 'charge', 'user', 'sender', 'reference', 'trans_code', 'tel',
        'nsp',
        'status',
    )


class MobileMoneyAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('tel', 'tracker_id', 'user__username', 'uuid')
    list_filter = ('request_date', 'response_status', 'nsp', 'request_type', 'request_status')
    list_display = (
        'id', 'tracker_id', 'request_type', 'request_status', 'response_code', 'response_status',
        'callback_status_code', 'is_complete', 'tel', 'nsp', 'amount', 'charge', 'request_date', 'invoice_number',
        'response_date', 'message', 'transaction_id', 'user', 'response_transaction_date',
        'user_auth', 'server_response', 'callback_server_response', 'provider', 'purpose', 'callback_response_date',
        'recipient', 'uuid',
    )


admin.site.register(MobileMoney, MobileMoneyAdmin)
admin.site.register(WalletModel, WalletModelAdmin)
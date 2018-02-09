from django.contrib import admin
from .models import WalletModel, MobileMoney
# Register your models here.

admin.site.register(
    WalletModel,
    list_display=(
        'id', 'description', 'information', 'amount', 'charge', 'user', 'sender', 'reference', 'trans_code', 'tel', 'nsp',
        'status',
    )
)

admin.site.register(
    MobileMoney,
    list_display=(
        'id', 'request_type', 'request_status', 'response_status', 'tel', 'nsp', 'amount', 'request_date',
        'response_date', 'message', 'transaction_id', 'user', 'response_transaction_date'
    )
)

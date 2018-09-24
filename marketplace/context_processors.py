from purse.models import WalletManager

wallet_manager = WalletManager()

def get_balance(reqest):
    user = request.user
    if user.is_authenticated:
        return wallet_manager.balance(user=user)
    else:
        return 0

def marketplace_context_processors(request):
    context = {
        'balance': get_balance(request)
    }
    return context

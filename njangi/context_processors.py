from blog.models import MainCategory
from main.core import NSP
from njangi.models import NjangiTree, UserAccountManager
from purse.models import WalletManager


wallet_manager = WalletManager()
account_manager = UserAccountManager()

def get_user_balance(request):
    user = request.user
    if user.is_authenticated:
        return wallet_manager.balance(user=user)
    else:
        return 0

def get_user_node(request):
    if request.user.is_authenticated:
        try:
            user_node = NjangiTree.objects.get(user=request.user)
            return user_node
        except NjangiTree.DoesNotExist:
            return NjangiTree.objects.none()
    else:
        return NjangiTree.objects.none()


def get_user_account_list(request):
    user_account_list = ""
    if request.user.is_authenticated:
        if request.user.user_account_id:
            user_account_list = account_manager.get_user_account_user_list(
                user_account_id=request.user.user_account_id
            )
        return user_account_list


def get_user_account(request):
        user_account = ""
        if request.user.is_authenticated:
            user_account = account_manager.get_user_account(request.user.user_account_id)
        return user_account


def njangi_context_processors(request):
    context = {
        'nsp_': NSP(),
        'user_node': get_user_node(request),
        'user_account': get_user_account(request),
        'user_account_list': get_user_account_list(request),
        'main_category_list': MainCategory.objects.filter(is_published=True),
        'account_balance': get_user_balance(request),
    }
    return context

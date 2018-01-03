from njangi.models import NjangiTree
from main.core import NSP


def get_user_node(request):
    if request.user.is_authenticated:
        try:
            user_node = NjangiTree.objects.get(user=request.user)
            return user_node
        except NjangiTree.DoesNotExist:
            return NjangiTree.objects.none()
    else:
        return NjangiTree.objects.none()


def njangi_context_processors(request):
    context = {
        'nsp_': NSP(),
        'user_node': get_user_node(request)
    }
    return context

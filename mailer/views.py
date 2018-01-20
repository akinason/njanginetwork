from django.http import JsonResponse


def index(request):
    from .utils import send
    response = send(request=request)

    return JsonResponse(data={})

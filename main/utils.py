import random
from django.contrib.auth import get_user_model


def get_admin_users():
    admins = get_user_model().objects.filter(is_admin=True)
    admin_list = []
    for admin in admins:
        admin_list.append(admin)
    random.shuffle(admin_list)
    return admin_list


def add_admin_sponsor_id_to_session(request):
    admin = get_admin_users()[0]
    request.session['sponsor_id'] = admin.sponsor_id
    return admin.sponsor_id


def add_sponsor_id_to_session(request):
    """
    Adds the sponsor id to session gotten from the request.
    :param: request
    :return: sponsor_id
    """
    if request.user.is_authenticated:
        sponsor_id = request.user.sponsor_id
        request.session['sponsor_id'] = sponsor_id
        return sponsor_id
    else:
        sponsor_id = request.GET.get('rid', False)
        if sponsor_id:
            try:
                # If a user exist with the given sponsor_id, add the sponsor_id to session.
                get_user_model().objects.filter(sponsor_id=sponsor_id).get()
                request.session['sponsor_id'] = sponsor_id
                return sponsor_id
            except get_user_model().DoesNotExist:
                # If the user with the provided sponsor_id does not exist, add an admin sponsor_id to session
                return add_admin_sponsor_id_to_session(request)
        else:
            # check if there is a sponsor_id in the session.
            if 'sponsor_id' in request.session:
                sponsor_id = request.session['sponsor_id']
                try:
                    # If a user exist with the given sponsor_id, return the sponsor_id
                    get_user_model().objects.filter(sponsor_id=sponsor_id).get()
                    return sponsor_id
                except get_user_model().DoesNotExist:
                    # If the user with the provided sponsor_id does not exist, add an admin sponsor_id to session
                    return add_admin_sponsor_id_to_session(request)
            else:
                # If not,add an admin sponsor_id to session
                return add_admin_sponsor_id_to_session(request)


def get_sponsor_id_from_session(request):
    if 'sponsor_id' in request.session:
        return request.session['sponsor_id']
    else:
        return add_sponsor_id_to_session(request)


def get_sponsor(request):
    return get_user_model().objects.filter(sponsor_id=get_sponsor_id_from_session(request)).get()


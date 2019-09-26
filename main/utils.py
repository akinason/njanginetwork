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


def add_admin_promoter_id_to_session(request):
    admin = get_admin_users()[0]
    request.session['promoter_id'] = admin.sponsor_id
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


def add_promoter_id_to_session(request):
    """
    Adds the promoter id to session gotten from the request.
    :param: request
    :return: promoter_id
    """
    if request.user.is_authenticated:
        promoter_id = request.user.sponsor_id
        request.session['promoter_id'] = promoter_id
        return promoter_id
    else:
        promoter_id = request.GET.get('pid', False)
        sponsor_id = request.GET.get('rid', False)
        # print(sponsor_id, promoter_id)
        if promoter_id:
            try:
                # If a user exist with the given promoter_id (sponsor_id), add the promoter_id to session.
                u = get_user_model().objects.filter(sponsor_id=promoter_id).get()
                request.session['promoter_id'] = promoter_id
                return promoter_id
            except get_user_model().DoesNotExist:
                # If the user with the provided promoter_id does not exist, add an admin sponsor_id to session
                return add_admin_promoter_id_to_session(request)
        elif sponsor_id:
            try:
                # if there is no promoter_id but exist a sponsor_id, consider the sponsor to be the promoter.
                get_user_model().objects.filter(sponsor_id=sponsor_id).get()
                request.session['promoter_id'] = sponsor_id
                return sponsor_id
            except get_user_model().DoesNotExist:
                # If the user with the provided sponsor_id does not exist, add an admin sponsor_id to session
                return add_admin_promoter_id_to_session(request)
        else:
            # check if there is a promoter_id in the session.
            if 'promoter_id' in request.session:
                promoter_id = request.session['promoter_id']
            if 'sponsor_id' in request.session:
                sponsor_id = request.session['sponsor_id']
                try:
                    # If a user exist with the given promoter_id (sponsor_id), return the sponsor_id
                    get_user_model().objects.filter(sponsor_id=promoter_id).get()
                    return promoter_id
                except get_user_model().DoesNotExist:
                    # If the user with the provided promoter_id (sponsor_id) does not exist, check
                    # for a user with the given sponsor_id  else add an admin sponsor_id to session
                    try:
                        if sponsor_id:
                            get_user_model().objects.filter(sponsor_id=sponsor_id).get()
                            return sponsor_id
                        else:
                            return add_admin_promoter_id_to_session(request)
                    except get_user_model().DoesNotExist:
                        return add_admin_promoter_id_to_session(request)
            else:
                # If not,add an admin promoter_id to session
                return add_admin_promoter_id_to_session(request)


def get_sponsor_id_from_session(request):
    # Extracts the sponsor_id from session. if it is not yet existing, it adds it to session.
    if 'sponsor_id' in request.session:
        return request.session['sponsor_id']
    else:
        return add_sponsor_id_to_session(request)


def get_promoter_id_from_session(request):
    # Extracts the promoter_id from session. if it is not yet existing, it adds it to session.
    if 'promoter_id' in request.session:
        return request.session['promoter_id']
    else:
        return add_promoter_id_to_session(request)


def get_sponsor(request):
    """
    This is the person under whom this new user will be placed in the network. In the case where the parameter
    'pid' is not present in the signup url, then its the person who referred the current user.
    :param request:
    :return: the user under whom the current user will be placed in the network or the user who referred the current
            user.
    """
    return get_user_model().objects.filter(sponsor_id=get_sponsor_id_from_session(request)).get()


def get_promoter(request):
    """
    This is the person who actually referred the user. This only exist if the url parameter "pid" is present.
    :param request:
    :return: the user who referred the current user.
    """
    return get_user_model().objects.filter(sponsor_id=get_promoter_id_from_session(request)).get()


def get_sponsor_using_sponsor_id(sponsor_id):
    try:
        return get_user_model().objects.get(pk=sponsor_id)
    except get_user_model().MultipleObjectsReturned:
        return get_user_model().objects.filter(pk=sponsor_id)[:1].get()
    except get_user_model().DoesNotExist:
        return get_admin_users()[0]

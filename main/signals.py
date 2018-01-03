from django.utils import translation
from .utils import add_sponsor_id_to_session, add_admin_sponsor_id_to_session


def add_logged_in_user_sponsor_id_to_session(sender, user, request, **kwargs):
    add_sponsor_id_to_session(request)


def remove_logged_in_user_sponsor_id_from_session(sender, user, request, **kwargs):
    add_admin_sponsor_id_to_session(request)


def set_default_user_language(sender, user, request, **kwargs):
    user_language = 'en'
    translation.activate(user_language)
    request.session[translation.LANGUAGE_SESSION_KEY] = user_language

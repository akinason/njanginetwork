from.utils import add_sponsor_id_to_session, add_admin_sponsor_id_to_session


def add_logged_in_user_sponsor_id_to_session(sender, user, request, **kwargs):
    add_sponsor_id_to_session(request)


def remove_logged_in_user_sponsor_id_from_session(sender, user, request, **kwargs):
    add_admin_sponsor_id_to_session(request)


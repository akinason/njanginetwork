
from njangi.core import create_user_levels, add_user_to_njangi_tree


def create_admin_user(username, password):
    from django.contrib.auth import get_user_model
    failed_reason = ''
    if get_user_model().objects.filter(username=username).exists():
        failed_reason = 'Username already exist.'
        return failed_reason
    else:
        user = get_user_model().objects.create(
            username=username, first_name='Awa', last_name='kinason', is_active=True,
            gender='male', is_admin=True, tel1='+23765397307', tel2='+237655916762'
        )
        user.set_password(password)
        user.sponsor_id = user.id
        user.level = 6
        user.set_unique_random_sponsor_id()
        user.set_unique_random_tel1_code()
        user.set_unique_random_tel2_code()
        user.set_unique_random_tel3_code()
        user.tel1_is_verified = True
        user.tel2_is_verified = True
        user.tel3_is_verified = True
        user.email_is_verified = True
        user.save()
        add_user_to_njangi_tree(user=user)
        create_user_levels(user=user)
        return user

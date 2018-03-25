from main.models import User
from njangi.models import UserAccountManager, UserAccountSubscriptionType
from njangi.tasks import process_subscription_update

manager = UserAccountManager()
subscription_type = UserAccountSubscriptionType()

def test_add_user():
    user1 = User.objects.get(username='gloxon')
    user2 = User.objects.get(username='admin')
    user3 = User.objects.get(username='muluh')
    user4 = User.objects.get(username='kinason')
    user5 = User.objects.get(username='penn')
    user1.user_account_id = None
    user2.user_account_id = None
    user3.user_account_id = None
    user4.user_account_id = None
    user5.user_account_id = None
    user1.save()
    user2.save()
    user3.save()
    user4.save()
    user5.save()
    print('adding user gloxon to the list')
    ua = manager.add_user_to_user_account(user=user1)
    print(ua, ua.related_users)

    print()

    print('adding user spirit to the list')
    ua2 = manager.add_user_to_user_account(user2, ua.id)
    print(ua2, ua2.related_users)

    print()

    print('adding user muluh to the list')
    ua3 = manager.add_user_to_user_account(user3, ua.id)
    print(ua3, ua3.related_users if ua3 else None)

    print()

    print('removing user gloxon from the list')
    ua4 = manager.remove_user_from_user_account(user1, ua.id)
    print(ua4, ua4.related_users)

    print()

    print('adding back user gloxon to the list')
    ua5 = manager.add_user_to_user_account(user1, ua.id)
    print(ua5, ua5.related_users if ua5 else None)

    print()

    print('adding user spirit to the list again')
    ua6 = manager.add_user_to_user_account(user2, ua.id)
    print(ua6, ua6.related_users if ua6 else None)

    print()

    print('printing list of users in this user list')
    print(len(manager.get_user_account_user_list(ua.id)))

    # print()
    # print('Updating the status of ua2')
    # ua7 = manager.update_subscription(user_account_id=ua2.id, package_id=1, subscription="monthly")
    # print(ua7, ua7.is_active)

    print()
    print('deactivating all accounts with overdue subscriptions.')
    print(manager.deactivate_over_due_subscriptions())

    print()
    print('adding user biim to the list')
    ua8 = manager.add_user_to_user_account(user4, ua.id)
    print(ua8, ua8.related_users if ua8 else None)

    print()
    print('check if user biim is in the list')
    ua9 = manager.user_is_in_list(user4.id, ua.id)
    print(ua9)

    print()
    print('check if user penn is in the list')
    ua10 = manager.user_is_in_list(user5.id, ua.id)
    print(ua10)

    print()
    print('extending existing subscription duration by 1month')
    r = process_subscription_update(
        user_id=user4.id, package_id=2, subscription_type=subscription_type.monthly(), nsp="mtn_wallet",
        user_account_id=user1.user_account_id
    )
    print(r)

    print()
    print('extending new subscription duration by 1month')
    r = process_subscription_update(
        user_id=user4.id, package_id=2, subscription_type=subscription_type.monthly(), nsp="mtn_wallet",
    )
    print(r)

if __name__ == '__main__':
    test_add_user()


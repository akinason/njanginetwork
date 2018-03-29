
from django.contrib.auth import get_user_model as UserModel
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from main.models import Notification


class NotificationManager:

    def __init__(self):
        self.model = Notification

    def create(self, notification_type, text, user_id, link=None):
        user = None
        notification = None

        try:
            user = UserModel().objects.get(pk=user_id)
        except UserModel().DoesNotExist:
            pass

        if user:
            notification = self.model.objects.create(
                type=notification_type, text=text, user=user
            )
            if link:
                notification.link = link
                notification.save()

        return notification

    def update(self, notification_id, is_read=True):
        try:
            notification = self.model.objects.get(pk=notification_id)
            notification.is_read = is_read
            notification.read_on = timezone.now()
            notification.save()
        except self.model.DoesNotExist:
            return False
        return True

    def get_notification(self, notification_id):
        # Returns the notification matching the notification_id or None if not found.
        notification = None

        try:
            notification = self.model.objects.get(pk=notification_id)
        except self.model.DoesNotExist:
            pass

        return notification

    def get_user_notifications(self, user_id, limit=None):
        # Returns the list of user notifications in descending order of date 'created_on'
        # Default limits to 10 notifications if there are not upto 10 unread notifications else the
        # total number of unread notifications.
        user = None
        try:
            user = UserModel().objects.get(pk=user_id)
        except UserModel().DoesNotExist:
            return self.model.objects.none()

        if not limit:
            unread_notification_count = self.model.objects.filter(is_read=False).count()
            if unread_notification_count > 10:
                limit = unread_notification_count
            else:
                limit = 10

        return self.model.objects.filter(user=user).order_by('-created_on')[:limit]

    def get_unread_notification_count(self, user_id):
        # Returns the count of unread notifications for a particular user
        user = None
        try:
            user = UserModel().objects.get(pk=user_id)
        except UserModel().DoesNotExist:
            return 0

        return self.model.objects.filter(user=user, is_read=False).count()

    def mark_notifications_as_read(self, user_id):
        notification_list = self.get_user_notifications(user_id=user_id)
        for obj in notification_list:
            obj.is_read = True
            obj.read_on = timezone.now()
            obj.save()
        return notification_list.count()

    class NotificationTypes:

        def __init__(self):
            self._contribution_received = 'contribution_received'
            self._contribution_failed = 'contribution_failed'
            self._contribution_paid = 'contribution_paid'
            self._wallet_load_failed = 'wallet_load_failed'
            self._wallet_withdraw_failed = 'wallet_withdraw_failed'
            self._wallet_load_success = 'wallet_load_success'
            self._wallet_withdraw_success = 'wallet_withdraw_success'
            self._subscription_failed = 'subscription_failed'
            self._subscription_success = 'subscription_success'

        def contribution_received(self):
            return self._contribution_received

        def contribution_paid(self):
            return self._contribution_paid

        def contribution_failed(self):
            return self._contribution_failed

        def wallet_load_success(self):
            return self._wallet_load_success

        def wallet_load_failed(self):
            return self._wallet_load_failed

        def wallet_withdraw_success(self):
            return self._wallet_withdraw_success

        def wallet_withdraw_failed(self):
            return self._wallet_withdraw_failed

        def subscription_success(self):
            return self._subscription_success

        def subscription_failed(self):
            return self._subscription_failed

    class Templates:

        def __init__(self):
            self.text = ''

        def contribution_failed(self, user_id, amount, level):
            self.text = _('Your level %(level)s contribution of %(amount)s  was unsuccessful.') % {
                'level': level, 'amount': amount
            }
            return NotificationManager().create(
                notification_type=NotificationManager.NotificationTypes().contribution_failed(),
                user_id=user_id, text=self.text
            )

        def withdrawal_failed(self, user_id, amount, nsp):
            self.text = _('Your %(nsp)s withdrawal of %(amount)s was not successful. Please try again.') % {
                'nsp': nsp.replace('_', ' ').upper(), 'amount': amount
            }
            return NotificationManager().create(
                notification_type=NotificationManager.NotificationTypes().wallet_withdraw_failed(),
                user_id=user_id, text=self.text
            )

        def transaction_failed(self, user_id, purpose, amount, nsp=None):
            if nsp:
                self.text = _('Your %(purpose)s of %(amount)s through %(nsp)s was not successful. Please try again') % {
                    'purpose': purpose.replace("_", " ").capitalize(), 'amount': amount, 'nsp': nsp.replace('_', ' ').upper()
                }
            else:
                self.text = _('Your %(purpose)s of %(amount)s was not successful. Please try again.') % {
                    'purpose': purpose.replace("_", " ").capitalize(), 'amount': amount
                }
            return NotificationManager().create(notification_type=purpose, user_id=user_id, text=self.text)

        def transaction_successful(self, user_id, purpose, amount, nsp=None):
            if nsp:
                self.text = _('Your %(purpose)s of %(amount)s through %(nsp)s was successful.') % {
                    'purpose': purpose.replace("_", " ").capitalize(), 'amount': amount, 'nsp': nsp.replace('_', ' ').upper()
                }
            else:
                self.text = _('Your %(purpose)s of %(amount)s was successful.') % {
                    'purpose': purpose.replace("_", " ").capitalize(), 'amount': amount
                }
            return NotificationManager().create(notification_type=purpose, user_id=user_id, text=self.text)

    notification_type = NotificationTypes()
    templates = Templates()


def notification():
    return NotificationManager()
import random
from main import notification
from django.contrib.auth import get_user_model as UserModel


def create_notifications(number=10):
    user = UserModel().objects.get(username='kinason')
    for x in range(1, number):
        item = notification.notification().templates.contribution_failed(
            user_id=user.id, amount=random.randint(1000, 20000), level=random.randint(1, 6)
        )
        print(item)




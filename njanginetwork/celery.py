import os
import datetime
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'njanginetwork.settings')

app = Celery('njanginetwork')
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django App Configs
# app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process_automatic_contributions': {
        'task': 'njangi.tasks.process_automatic_contributions',
        'schedule': crontab(hour=0, minute=0),
    },
    'deactivate_users_with_past_due_contribution': {
        'task': 'njangi.tasks.deactivate_users_with_past_due_contribution',
        'schedule': crontab(hour=0, minute=3),
    },
    'send_contribution_due_reminder': {
        'task': 'njangi.tasks.send_contribution_due_reminder',
        'schedule': crontab(hour=0, minute=5),
    },
    'deactivate_users_with_due_package_subscription': {
        'task': 'njangi.tasks.deactivate_users_with_due_package_subscription',
        'schedule': crontab(hour=0, minute=6),
    },
    'send_package_subscription_reminder': {
        'task': 'njangi.tasks.send_package_subscription_reminder',
        'schedule': crontab(hour=0, minute=7),
    },

}


from __future__ import absolute_import, unicode_literals

import os
from njanginetwork.celery import app as celery_app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


__all__ = ['celery_app']
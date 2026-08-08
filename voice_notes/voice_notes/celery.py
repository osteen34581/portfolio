import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_notes.settings')
app = Celery('voice_notes')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.autodiscover_tasks()

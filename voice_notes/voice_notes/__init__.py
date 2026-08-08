from .celery import app as celery_app

# Expose celery app as `celery_app` for Django/Celery integration
__all__ = ('celery_app',)

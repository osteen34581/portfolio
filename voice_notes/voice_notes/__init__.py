try:
	from .celery import app as celery_app
	__all__ = ('celery_app',)
except Exception:
	# If Celery is not installed or celery app cannot be imported during
	# development, avoid raising on Django startup. Celery is optional; when
	# present the app will be exposed as `celery_app`.
	celery_app = None
	__all__ = ()

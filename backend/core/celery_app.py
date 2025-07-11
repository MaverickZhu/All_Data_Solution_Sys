from celery import Celery
from backend.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.processing.tasks"],  # Points to the module where tasks are defined
)

celery_app.conf.update(
    task_track_started=True,
) 
from celery import Celery

REDIS_URL = "redis://default:rBcCMutrfQsUCxAJmJxbqCAMgspwWfUI@shortline.proxy.rlwy.net:36021/0"

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)

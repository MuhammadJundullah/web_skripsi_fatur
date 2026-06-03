import os
from urllib.parse import quote, unquote

from celery import Celery


def normalize_redis_url(raw_url: str) -> str:
    if not raw_url:
        return "redis://default:rBcCMutrfQsUCxAJmJxbqCAMgspwWfUI@shortline.proxy.rlwy.net:36021/2"

    if not raw_url.startswith(("redis://", "rediss://")):
        return raw_url

    scheme, remainder = raw_url.split("://", 1)
    if "@" not in remainder:
        return raw_url

    userinfo, host_and_path = remainder.rsplit("@", 1)
    if "/" in host_and_path:
        host, path = host_and_path.split("/", 1)
        path = f"/{path}"
    else:
        host = host_and_path
        path = ""

    if ":" in userinfo:
        username, password = userinfo.split(":", 1)
        encoded_userinfo = (
            f"{quote(unquote(username), safe='')}:{quote(unquote(password), safe='')}"
        )
    else:
        encoded_userinfo = quote(unquote(userinfo), safe="")

    return f"{scheme}://{encoded_userinfo}@{host}{path}"


REDIS_URL = normalize_redis_url(
    os.getenv(
        "REDIS_URL",
        "redis://default:rBcCMutrfQsUCxAJmJxbqCAMgspwWfUI@shortline.proxy.rlwy.net:36021/2",
    )
)

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)

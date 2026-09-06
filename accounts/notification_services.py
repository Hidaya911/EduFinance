"""Read-only notification helpers for authenticated dashboard previews."""

from urllib.parse import urlsplit

from django.conf import settings
from django.urls import Resolver404, resolve
from pymongo import ASCENDING, DESCENDING, MongoClient

from .context_processors import _notification_id_variants
from .models import Notification


UNSAFE_ROUTE_MARKERS = {
    "approve", "cancel", "create", "delete", "edit", "logout",
    "process", "reject", "send", "submit", "toggle", "void",
}


def _safe_internal_link(value):
    link = str(value or "").strip()
    if not link or not link.startswith("/") or link.startswith("//") or "\\" in link:
        return ""

    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return ""

    try:
        match = resolve(parsed.path)
    except Resolver404:
        return ""

    route_name = str(match.url_name or "").lower()
    if any(marker in route_name.split("_") for marker in UNSAFE_ROUTE_MARKERS):
        return ""
    return link


def get_user_notification_preview(user, limit=5):
    """Return unread-first recent notifications owned by ``user``."""
    if not user or not user.is_authenticated:
        return []

    client = None
    try:
        client = MongoClient(
            settings.MONGO_URI if hasattr(settings, "MONGO_URI")
            else settings.DATABASES["default"]["CLIENT"]["host"]
        )
        database = client[settings.DATABASES["default"]["NAME"]]
        recipient_ids = _notification_id_variants(database, user.pk)
        cursor = (
            database[Notification._meta.db_table]
            .find({"user_id": {"$in": recipient_ids}})
            .sort([("is_read", ASCENDING), ("created_at", DESCENDING)])
            .limit(max(1, min(int(limit), 5)))
        )
        return [
            {
                "title": str(item.get("title") or "Notification"),
                "message": str(item.get("message") or ""),
                "created_at": item.get("created_at"),
                "is_read": bool(item.get("is_read", False)),
                "link": _safe_internal_link(item.get("link")),
            }
            for item in cursor
        ]
    except Exception:
        return []
    finally:
        if client is not None:
            client.close()

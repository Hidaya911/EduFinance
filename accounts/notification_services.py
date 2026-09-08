"""Read-only notification helpers for authenticated dashboard previews."""

from urllib.parse import urlsplit, parse_qs

from django.db import connection
from django.urls import Resolver404, resolve
from pymongo import ASCENDING, DESCENDING

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

    try:
        parsed = urlsplit(link)
    except ValueError:
        return ""
    if parse_qs(parsed.query).get("mark_all_read"):
        return ""
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


def _load_notifications(user, limit=5, include_count=False):
    """Use the backend connection and the existing legacy recipient-ID mapping."""
    result = {"latest_notifications": [], "unread_notifications_count": 0}
    if not user or not user.is_authenticated:
        return result
    try:
        database = connection.database
        recipient_ids = _notification_id_variants(database, user.pk)
        collection = database[Notification._meta.db_table]
        owner = {"user_id": {"$in": recipient_ids}}
        cursor = (
            collection.find(owner, {"title": 1, "message": 1, "created_at": 1, "is_read": 1, "link": 1})
            .sort([("is_read", ASCENDING), ("created_at", DESCENDING), ("_id", DESCENDING)])
            .limit(max(1, min(int(limit), 5)))
        )
        result["latest_notifications"] = [
            {
                "title": str(item.get("title") or "Notification"),
                "message": str(item.get("message") or ""),
                "created_at": item.get("created_at"),
                "is_read": bool(item.get("is_read", False)),
                "link": _safe_internal_link(item.get("link")),
            }
            for item in cursor
        ]
        if include_count:
            result["unread_notifications_count"] = collection.count_documents({**owner, "is_read": False})
        return result
    except Exception:
        # Preserve the existing preview's graceful failure behavior.
        return {"latest_notifications": [], "unread_notifications_count": 0}


def get_user_notification_preview(user, limit=5):
    """Keep the dashboard's existing preview API and read-only behavior."""
    return _load_notifications(user, limit)["latest_notifications"]


def get_user_notification_center(user):
    """Five unread-first notifications plus the full unread count for the navbar."""
    return _load_notifications(user, include_count=True)

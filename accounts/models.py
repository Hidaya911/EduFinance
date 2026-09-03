from django.conf import settings
from django.db import models
from django_mongodb_backend.fields import ObjectIdField


# ============================================================
# LEGACY / ACCOUNTS USER DOCUMENT
# ============================================================

class User(models.Model):
    _id = ObjectIdField(
        primary_key=True,
        auto_created=True,
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.title} - "
            f"{self.user.username}"
        )


# ============================================================
# NOTIFICATION PREFERENCES
# ============================================================

class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    email_notifications = models.BooleanField(
        default=True,
    )

    system_alerts = models.BooleanField(
        default=True,
    )

    role_updates = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return (
            f"Preferences for "
            f"{self.user.username}"
        )
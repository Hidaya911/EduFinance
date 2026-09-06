from django.conf import settings
from django.db import models

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    record_repr = models.CharField(max_length=255, blank=True, null=True, help_text="String representation of the record")
    changes = models.TextField(blank=True, null=True, help_text="JSON or descriptive text of what changed")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"[{self.timestamp}] {username} - {self.action} {self.model_name} ({self.record_repr})"
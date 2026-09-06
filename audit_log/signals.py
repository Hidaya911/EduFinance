from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditLog
from .middleware import get_current_user
from school_config.models import Grade, SchoolClass

@receiver(post_save, sender=Grade)
def log_grade_save(sender, instance, created, **kwargs):
    current_user = get_current_user()
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        user=current_user,
        action=action,
        model_name='Grade',
        record_id=str(instance.pk),
        record_repr=str(instance),
        changes=f"Grade '{instance.name}' was {'created' if created else 'updated'}."
    )

@receiver(post_delete, sender=Grade)
def log_grade_delete(sender, instance, **kwargs):
    current_user = get_current_user()
    AuditLog.objects.create(
        user=current_user,
        action='DELETE',
        model_name='Grade',
        record_id=str(instance.pk),
        record_repr=str(instance),
        changes=f"Grade '{instance.name}' was deleted."
    )
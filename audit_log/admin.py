from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'record_id')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'record_repr', 'changes')
    readonly_fields = ('user', 'action', 'model_name', 'record_id', 'record_repr', 'changes', 'ip_address', 'timestamp')
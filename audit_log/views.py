from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import AuditLog

def can_view_audit_logs(user):
    """Accessible exclusively by Super Administrator and Auditor roles."""
    return user.is_authenticated and (
        user.is_superuser or
        user.groups.filter(name__in=['Super Admin', 'Super Administrator', 'Auditor']).exists() or
        getattr(user, 'role', None) in ['Super Administrator', 'Super Admin', 'Auditor']
    )

@login_required
@user_passes_test(can_view_audit_logs)
def audit_log_list_view(request):
    logs_qs = AuditLog.objects.select_related('user').all()

    # Filter parameters
    q_search = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q_search:
        logs_qs = logs_qs.filter(
            Q(user__username__icontains=q_search) |
            Q(user__email__icontains=q_search) |
            Q(model_name__icontains=q_search) |
            Q(record_repr__icontains=q_search) |
            Q(changes__icontains=q_search)
        )

    if action_filter:
        logs_qs = logs_qs.filter(action=action_filter)

    if date_from:
        logs_qs = logs_qs.filter(timestamp__date__gte=date_from)

    if date_to:
        logs_qs = logs_qs.filter(timestamp__date__lte=date_to)

    # Pagination (25 logs per page)
    paginator = Paginator(logs_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_TYPES,
        'filters': {
            'q': q_search,
            'action': action_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'audit_log/audit_log_list.html', context)
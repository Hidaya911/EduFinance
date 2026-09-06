from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from payables.dashboard_services import get_dashboard_context


def base_preview_view(request):
    return render(request, "accounts/preview.html")


@login_required(login_url="accounts:login")
def dashboard_view(request):
    return render(
        request,
        "dashboard.html",
        get_dashboard_context(request.user),
    )

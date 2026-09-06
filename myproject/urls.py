"""
URL configuration for EduFinance.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    # ========================================================
    # DJANGO ADMIN
    # ========================================================

    path(
        "admin/",
        admin.site.urls,
    ),

    # ========================================================
    # DEVELOPER 1 — ACCOUNTS / AUTHENTICATION
    # ========================================================
   path('', RedirectView.as_view(url='/login/', permanent=False)),
    path(
        "",
        include("accounts.urls"),
    ),

    # ========================================================
    # SHARED BASE PREVIEW
    # ========================================================

    path(
        "preview/",
        views.base_preview_view,
        name="base_preview",
    ),

    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard",
    ),

    # ========================================================
    # DEVELOPER 2 — ROUTES
    # ========================================================

    path(
        "students/",
        include("students.urls"),
    ),

    path(
    "billing/",
    include("billing.urls"),
),

    # ========================================================
    # DEVELOPER 3 — FINANCE / PAYABLES
    # ========================================================

    path(
        "finance/",
        include("payables.urls"),
    ),

    # ========================================================
    # SCHOOL CONFIGURATION
    # ========================================================

    path(
        "school/",
        include("school_config.urls"),
    ),

    path(
        "audit-log/",
        include("audit_log.urls"),
    ),


    path('', include('accounts.core.urls')),
]

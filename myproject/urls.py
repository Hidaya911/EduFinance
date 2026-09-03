"""
URL configuration for EduFinance.
"""

from django.contrib import admin
from django.urls import include, path

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
    #
    # Keep Accounts mounted at the project root.
    # Any new routes added by the teammate inside
    # accounts/urls.py are automatically included here.
    #
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

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
    # DEVELOPER 2 — STUDENTS / GUARDIANS
    # ========================================================

    path(
        "students/",
        include("students.urls"),
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
]
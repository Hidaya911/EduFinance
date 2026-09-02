"""
URL configuration for EduFinance.
"""

from django.contrib import admin
from django.urls import include, path

from . import views


urlpatterns = [

    # Django admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Developer 1 - Accounts / Authentication
    path(
        "",
        include("accounts.urls"),
    ),

    # Developer 1 - Shared Base Preview
    path(
        "preview/",
        views.base_preview_view,
        name="base_preview",
    ),

    # Developer 1 - Dashboard
    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard",
    ),

    # Developer 3 - Finance / Payables
    path(
        "finance/",
        include("payables.urls"),
    ),

    # School configuration
    path(
        "school/",
        include("school_config.urls"),
    ),

]
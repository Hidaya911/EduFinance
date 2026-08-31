"""
URL configuration for EduFinance.
"""

from django.contrib import admin
from django.urls import include, path


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

    # Developer 3 - Expenses / Payables
    path(
        "finance/",
        include("payables.urls"),
    ),

    path(
    "school/",
    include(
        "school_config.urls"
    ),
),

]
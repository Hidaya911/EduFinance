from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    # -----------------------------
    # Students
    # -----------------------------
    path(
        "",
        views.student_list,
        name="student_list",
    ),

    path(
        "create/",
        views.student_create,
        name="student_create",
    ),

    # -----------------------------
    # Guardians
    # IMPORTANT:
    # Keep these BEFORE <student_id> routes
    # -----------------------------
    path(
        "guardians/",
        views.guardian_list,
        name="guardian_list",
    ),

    path(
        "guardians/create/",
        views.guardian_create,
        name="guardian_create",
    ),

    path(
        "guardians/<str:guardian_id>/edit/",
        views.guardian_edit,
        name="guardian_edit",
    ),

    path(
        "guardians/<str:guardian_id>/delete/",
        views.guardian_delete,
        name="guardian_delete",
    ),

    # -----------------------------
    # Student dynamic routes
    # Keep these LAST
    # -----------------------------
    path(
        "<str:student_id>/edit/",
        views.student_edit,
        name="student_edit",
    ),

    path(
        "<str:student_id>/delete/",
        views.student_delete,
        name="student_delete",
    ),

    path(
        "<str:student_id>/",
        views.student_financial_profile,
        name="student_financial_profile",
    ),
]


    # -----------------------------
    # The reason the Guardian URLs must come before: "<str:student_id>/" is that Django checks URLs from top to bottom.
    # If this came first: path("<str:student_id>/", ...) , then going to: /students/guardians/ , could make Django think: student_id = "guardians" which is wrong.
    # -----------------------------
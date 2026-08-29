from django.urls import path

from . import views


app_name = "payables"


urlpatterns = [
    path(
        "expense-categories/",
        views.expense_category_list,
        name="expense_category_list",
    ),

    path(
        "expense-categories/create/",
        views.expense_category_create,
        name="expense_category_create",
    ),

    path(
        "expense-categories/<str:pk>/edit/",
        views.expense_category_edit,
        name="expense_category_edit",
    ),

    path(
        "expense-categories/<str:pk>/toggle/",
        views.expense_category_toggle,
        name="expense_category_toggle",
    ),

    path(
    "suppliers/",
    views.supplier_list,
    name="supplier_list",
),

path(
    "suppliers/create/",
    views.supplier_create,
    name="supplier_create",
),

path(
    "suppliers/<str:pk>/",
    views.supplier_detail,
    name="supplier_detail",
),

path(
    "suppliers/<str:pk>/edit/",
    views.supplier_edit,
    name="supplier_edit",
),

path(
    "suppliers/<str:pk>/toggle/",
    views.supplier_toggle,
    name="supplier_toggle",
),


]
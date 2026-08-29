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


path(
    "supplier-bills/",
    views.supplier_bill_list,
    name="supplier_bill_list",
),

path(
    "supplier-bills/create/",
    views.supplier_bill_create,
    name="supplier_bill_create",
),

path(
    "supplier-bills/<str:pk>/",
    views.supplier_bill_detail,
    name="supplier_bill_detail",
),

path(
    "supplier-bills/<str:pk>/edit/",
    views.supplier_bill_edit,
    name="supplier_bill_edit",
),

path(
    "supplier-bills/<str:pk>/toggle-cancel/",
    views.supplier_bill_toggle_cancel,
    name="supplier_bill_toggle_cancel",
),



# ============================================================
# SUPPLIER PAYMENTS
# ============================================================

path(
    "supplier-payments/",
    views.supplier_payment_list,
    name="supplier_payment_list",
),

path(
    "supplier-payments/create/",
    views.supplier_payment_create,
    name="supplier_payment_create",
),

path(
    "supplier-payments/<str:pk>/void/",
    views.supplier_payment_void,
    name="supplier_payment_void",
),


]
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


# ============================================================
# EXPENSES
# ============================================================

path(
    "expenses/",
    views.expense_list,
    name="expense_list",
),

path(
    "expenses/create/",
    views.expense_create,
    name="expense_create",
),

path(
    "expenses/<str:pk>/",
    views.expense_detail,
    name="expense_detail",
),

path(
    "expenses/<str:pk>/edit/",
    views.expense_edit,
    name="expense_edit",
),

path(
    "expenses/<str:pk>/void/",
    views.expense_void,
    name="expense_void",
),



# ============================================================
# EMPLOYEE FINANCIAL RECORDS
# ============================================================

path(
    "employee-financial-records/",
    views.employee_financial_list,
    name="employee_financial_list",
),

path(
    "employee-financial-records/create/",
    views.employee_financial_create,
    name="employee_financial_create",
),

path(
    "employee-financial-records/<str:pk>/",
    views.employee_financial_detail,
    name="employee_financial_detail",
),

path(
    "employee-financial-records/<str:pk>/edit/",
    views.employee_financial_edit,
    name="employee_financial_edit",
),

path(
    "employee-financial-transactions/create/",
    views.employee_financial_transaction_create,
    name=
        "employee_financial_transaction_create",
),

path(
    "employee-financial-transactions/<str:pk>/void/",
    views.employee_financial_transaction_void,
    name=
        "employee_financial_transaction_void",
),



# ============================================================
# APPROVAL WORKFLOW
# ============================================================

path(
    "approvals/",
    views.approval_list,
    name="approval_list",
),

path(
    "approvals/create/",
    views.approval_create,
    name="approval_create",
),

path(
    "approvals/<str:pk>/",
    views.approval_detail,
    name="approval_detail",
),

path(
    "approvals/<str:pk>/edit/",
    views.approval_edit,
    name="approval_edit",
),

path(
    "approvals/<str:pk>/submit/",
    views.approval_submit,
    name="approval_submit",
),

path(
    "approvals/<str:pk>/approve/",
    views.approval_approve,
    name="approval_approve",
),

path(
    "approvals/<str:pk>/reject/",
    views.approval_reject,
    name="approval_reject",
),

path(
    "approvals/<str:pk>/process/",
    views.approval_process,
    name="approval_process",
),


# ============================================================
# DISCOUNTS
# ============================================================

path(
    "discounts/",
    views.discount_list,
    name="discount_list",
),

path(
    "discounts/create/",
    views.discount_create,
    name="discount_create",
),

path(
    "discounts/<str:pk>/",
    views.discount_detail,
    name="discount_detail",
),

path(
    "discounts/<str:pk>/edit/",
    views.discount_edit,
    name="discount_edit",
),

path(
    "discounts/<str:pk>/submit/",
    views.discount_submit,
    name="discount_submit",
),

path(
    "discounts/<str:pk>/cancel/",
    views.discount_cancel,
    name="discount_cancel",
),

]
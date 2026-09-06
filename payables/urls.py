from django.urls import path

from . import payment_reminder_views

from . import views
from . import overdue_views
from . import report_views


app_name = "payables"


urlpatterns = [

    # ============================================================
    # REPORTS
    # ============================================================

    path(
        "reports/",
        report_views.reports_hub,
        name="reports_hub",
    ),

    path(
        "reports/<slug:slug>/",
        report_views.report_detail,
        name="report_detail",
    ),

    path(
        "reports/<slug:slug>/export/csv/",
        report_views.report_csv_export,
        name="report_csv_export",
    ),

    # ============================================================
    # EXPENSE CATEGORIES
    # ============================================================

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


    # ============================================================
    # SUPPLIERS
    # ============================================================

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


    # ============================================================
    # SUPPLIER BILLS
    # ============================================================

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
        name="employee_financial_transaction_create",
    ),

    path(
        "employee-financial-transactions/<str:pk>/void/",
        views.employee_financial_transaction_void,
        name="employee_financial_transaction_void",
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


    # ============================================================
    # SCHOLARSHIPS
    # ============================================================

    path(
        "scholarships/",
        views.scholarship_list,
        name="scholarship_list",
    ),

    path(
        "scholarships/create/",
        views.scholarship_create,
        name="scholarship_create",
    ),

    path(
        "scholarships/<str:pk>/",
        views.scholarship_detail,
        name="scholarship_detail",
    ),

    path(
        "scholarships/<str:pk>/edit/",
        views.scholarship_edit,
        name="scholarship_edit",
    ),

    path(
        "scholarships/<str:pk>/submit/",
        views.scholarship_submit,
        name="scholarship_submit",
    ),

    path(
        "scholarships/<str:pk>/cancel/",
        views.scholarship_cancel,
        name="scholarship_cancel",
    ),


    # ============================================================
    # FINANCIAL ASSISTANCE
    # ============================================================

    path(
        "financial-assistance/",
        views.financial_assistance_list,
        name="financial_assistance_list",
    ),

    path(
        "financial-assistance/create/",
        views.financial_assistance_create,
        name="financial_assistance_create",
    ),

    path(
        "financial-assistance/<str:pk>/",
        views.financial_assistance_detail,
        name="financial_assistance_detail",
    ),

    path(
        "financial-assistance/<str:pk>/edit/",
        views.financial_assistance_edit,
        name="financial_assistance_edit",
    ),

    path(
        "financial-assistance/<str:pk>/submit/",
        views.financial_assistance_submit,
        name="financial_assistance_submit",
    ),

    path(
        "financial-assistance/<str:pk>/cancel/",
        views.financial_assistance_cancel,
        name="financial_assistance_cancel",
    ),


    # ============================================================
    # REFUNDS
    # ============================================================

    path(
        "refunds/",
        views.refund_list,
        name="refund_list",
    ),

    path(
        "refunds/create/",
        views.refund_create,
        name="refund_create",
    ),

    path(
        "refunds/<str:pk>/",
        views.refund_detail,
        name="refund_detail",
    ),

    path(
        "refunds/<str:pk>/edit/",
        views.refund_edit,
        name="refund_edit",
    ),

    path(
        "refunds/<str:pk>/submit/",
        views.refund_submit,
        name="refund_submit",
    ),

    path(
        "refunds/<str:pk>/cancel/",
        views.refund_cancel,
        name="refund_cancel",
    ),




    # ============================================================
    # OVERDUE TRACKING
    # ============================================================

    path(
        "overdue/",
        overdue_views.overdue_list,
        name="overdue_list",
    ),




    # ============================================================
# PAYMENT REMINDERS
# ============================================================

path(
    "payment-reminders/",
    payment_reminder_views.payment_reminder_list,
    name="payment_reminder_list",
),

path(
    "payment-reminders/create/",
    payment_reminder_views.payment_reminder_create,
    name="payment_reminder_create",
),

path(
    "payment-reminders/<str:pk>/",
    payment_reminder_views.payment_reminder_detail,
    name="payment_reminder_detail",
),

path(
    "payment-reminders/<str:pk>/edit/",
    payment_reminder_views.payment_reminder_edit,
    name="payment_reminder_edit",
),

path(
    "payment-reminders/<str:pk>/send/",
    payment_reminder_views.payment_reminder_send,
    name="payment_reminder_send",
),

path(
    "payment-reminders/<str:pk>/cancel/",
    payment_reminder_views.payment_reminder_cancel,
    name="payment_reminder_cancel",
),
]

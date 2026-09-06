"""Read-only composition helpers for the main financial dashboard."""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from accounts.notification_services import get_user_notification_preview
from school_config.models import School

from .models import (
    ApprovalRequest, Discount, Expense, ExpenseCategory,
    FinancialAssistanceRequest, PaymentReminder, Refund, Scholarship,
    Supplier, SupplierBill, SupplierPayment,
)
from .overdue_services import summarize_overdue_rows
from .overdue_views import get_student_invoice_overdue_rows
from .report_services import (
    get_report_definition,
    get_reports_catalog,
    summarize_expenses,
)


ZERO = Decimal("0.00")


def _money(value):
    return f"{value or ZERO:,.2f}"


def _percent(numerator, denominator):
    if not denominator:
        return 0
    return max(0, min(100, round((numerator / denominator) * 100)))


def _month_keys(today, count=6):
    keys, year, month = [], today.year, today.month
    for _ in range(count):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(keys))


def _display_user(user):
    if not user:
        return "Unknown user"
    name = user.get_full_name().strip()
    return name or user.get_username()


def _can(user, permission):
    return bool(user and user.is_authenticated and user.has_perm(permission))


def _readiness():
    catalog = get_reports_catalog()
    return {
        "catalog": catalog,
        "revenue_ready": get_report_definition("monthly-revenue")["status"] == "ready",
        "collections_ready": get_report_definition("fee-collection")["status"] == "ready",
        "overdue_ready": get_report_definition("overdue-report")["status"] == "ready",
        "payments_ready": get_report_definition("payment-report")["status"] == "ready",
        "installments_ready": get_report_definition("installment-report")["status"] == "ready",
    }


def get_dashboard_context(user):
    """Build the dashboard from verified records without mutating any model."""
    now, today = timezone.localtime(), timezone.localdate()
    school = School.objects.first()
    currency = school.default_currency if school and school.default_currency else "USD"
    academic_year = school.current_academic_year.strip() if school and school.current_academic_year else "Not configured"
    readiness = _readiness()

    expenses = list(Expense.objects.all())
    categories = {str(item.pk): item.name for item in ExpenseCategory.objects.all()}
    bills = list(SupplierBill.objects.all())
    supplier_payments = list(SupplierPayment.objects.all())
    suppliers = {str(item.pk): item.name for item in Supplier.objects.all()}
    scholarships = list(Scholarship.objects.all())
    discounts = list(Discount.objects.all())
    refunds = list(Refund.objects.all())
    assistance = list(FinancialAssistanceRequest.objects.all())
    approvals = list(ApprovalRequest.objects.all())
    reminders = list(PaymentReminder.objects.all())
    important_notifications = get_user_notification_preview(user, limit=5)

    expense_summary = summarize_expenses(expenses, today)
    active_expenses = expense_summary["active"]
    total_expenses = expense_summary["active_total"]
    current_month = expense_summary["current_month"]
    month_expenses = expense_summary["current_month_total"]

    month_totals, category_totals = defaultdict(Decimal), defaultdict(Decimal)
    for item in active_expenses:
        month_totals[item.expense_date.strftime("%Y-%m")] += item.amount or ZERO
        category_totals[str(item.category_id)] += item.amount or ZERO

    monthly_expenses = [{"label": date(int(key[:4]), int(key[5:]), 1).strftime("%b"), "year": key[:4], "amount": month_totals[key]} for key in _month_keys(today)]
    max_month_expense = max((item["amount"] for item in monthly_expenses), default=ZERO)
    for item in monthly_expenses:
        item["height"] = _percent(item["amount"], max_month_expense)
        item["formatted"] = _money(item["amount"])

    expense_distribution = [
        {"name": categories.get(category_id, "Unassigned"), "amount": amount, "formatted": _money(amount), "percent": _percent(amount, total_expenses)}
        for category_id, amount in sorted(category_totals.items(), key=lambda pair: pair[1], reverse=True)[:5]
    ]

    active_bills = [item for item in bills if item.status != SupplierBill.Status.CANCELLED]
    payable_total = sum((item.total_amount or ZERO for item in active_bills), ZERO)
    payable_paid = sum((item.amount_paid or ZERO for item in active_bills), ZERO)
    payable_remaining = sum((item.remaining_amount or ZERO for item in active_bills), ZERO)
    overdue_bills = [item for item in active_bills if item.status == SupplierBill.Status.OVERDUE]
    overdue_payable_amount = sum((item.remaining_amount or ZERO for item in overdue_bills), ZERO)
    posted_supplier_payments = [item for item in supplier_payments if item.status == SupplierPayment.Status.POSTED]

    scholarship_active = [item for item in scholarships if item.status in (Scholarship.Status.APPROVED, Scholarship.Status.APPLIED)]
    scholarship_fixed = [item for item in scholarship_active if item.value_type == Scholarship.ValueType.FIXED_AMOUNT]
    discount_applied = [item for item in discounts if item.status == Discount.Status.APPLIED]
    pending_approvals = [item for item in approvals if item.status in (ApprovalRequest.Status.REQUESTED, ApprovalRequest.Status.PENDING)]
    pending_approvals.sort(key=lambda item: item.submitted_at or item.created_at, reverse=True)

    overdue_rows = list(get_student_invoice_overdue_rows())
    overdue_summary = summarize_overdue_rows(overdue_rows)
    recent_expenses = sorted(expenses, key=lambda item: item.updated_at, reverse=True)[:6]
    recent_supplier_payments = sorted(posted_supplier_payments, key=lambda item: item.payment_date, reverse=True)[:4]
    recent_reminders = sorted(reminders, key=lambda item: item.updated_at, reverse=True)[:4]
    report_counts = readiness["catalog"]["counts"]

    quick_actions = [
        {"label": "Create expense", "detail": "Record an operating cost", "icon": "bi-plus-circle", "url": reverse("payables:expense_create"), "show": _can(user, "payables.add_expense"), "primary": True},
        {"label": "View overdue", "detail": "Open student receivables risk", "icon": "bi-exclamation-diamond", "url": reverse("payables:overdue_list"), "show": True},
        {"label": "Approvals", "detail": "Review the financial queue", "icon": "bi-check2-square", "url": reverse("payables:approval_list"), "show": _can(user, "payables.view_approvalrequest")},
        {"label": "Reports", "detail": "Open financial intelligence", "icon": "bi-bar-chart-line", "url": reverse("payables:reports_hub"), "show": True},
    ]

    return {
        "greeting": "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening",
        "display_name": _display_user(user), "as_of": now,
        "currency_code": currency, "academic_year": academic_year, "readiness": readiness,
        "primary_kpis": [
            {"label": "Expected revenue", "value": "Integration pending", "detail": "Student invoice source unavailable", "icon": "bi-graph-up-arrow", "tone": "blue", "available": False},
            {"label": "Total collected", "value": "Integration pending", "detail": "Student payment source unavailable", "icon": "bi-bank", "tone": "green", "available": False},
            {"label": "Outstanding", "value": "Integration pending", "detail": "Student receivables unavailable", "icon": "bi-hourglass-split", "tone": "amber", "available": False},
            {"label": "Overdue amount", "value": "Integration pending", "detail": "Student invoice due dates unavailable", "icon": "bi-exclamation-circle", "tone": "red", "available": False},
            {"label": "Current month revenue", "value": "Integration pending", "detail": "No recognized revenue source", "icon": "bi-calendar2-week", "tone": "blue", "available": False},
            {"label": "Current month expenses", "value": _money(month_expenses), "detail": f"{len(current_month)} active record(s)", "icon": "bi-wallet2", "tone": "violet", "available": True},
            {"label": "Net financial position", "value": "Integration pending", "detail": "Requires verified revenue and expense data", "icon": "bi-intersect", "tone": "slate", "available": False},
        ],
        "total_expenses": _money(total_expenses), "expense_count": len(active_expenses),
        "month_expenses": _money(month_expenses), "monthly_expenses": monthly_expenses,
        "has_monthly_expenses": any(item["amount"] for item in monthly_expenses),
        "expense_distribution": expense_distribution, "has_expense_distribution": bool(expense_distribution),
        "overdue_summary": overdue_summary,
        "adjustments": {
            "scholarship_records": len(scholarships),
            "active_scholarships": len(scholarship_active),
            "fixed_scholarship_total": _money(sum((item.value or ZERO for item in scholarship_fixed), ZERO)),
            "pending_scholarships": sum(item.status == Scholarship.Status.PENDING_APPROVAL for item in scholarships),
            "discount_records": len(discounts),
            "applied_discounts": len(discount_applied),
            "pending_discounts": sum(item.status == Discount.Status.PENDING_APPROVAL for item in discounts),
            "refund_requests": len(refunds),
            "refund_active_total": _money(sum((item.amount or ZERO for item in refunds if item.status != Refund.Status.CANCELLED), ZERO)),
            "pending_refunds": sum(item.status in (Refund.Status.REQUESTED, Refund.Status.PENDING_APPROVAL) for item in refunds),
            "approved_refunds": sum(item.status == Refund.Status.APPROVED for item in refunds),
            "processed_refunds": sum(item.status == Refund.Status.PROCESSED for item in refunds),
            "assistance_total": len(assistance),
            "assistance_submitted": sum(item.status == FinancialAssistanceRequest.Status.SUBMITTED for item in assistance),
            "assistance_review": sum(item.status == FinancialAssistanceRequest.Status.UNDER_REVIEW for item in assistance),
            "assistance_approved": sum(item.status == FinancialAssistanceRequest.Status.APPROVED for item in assistance),
        },
        "pending_approval_count": len(pending_approvals),
        "approval_preview": [{"pk": item.pk, "number": item.request_number, "type": item.get_operation_type_display(), "title": item.title, "amount": _money(item.amount) if item.amount is not None else "Not monetary", "requester": _display_user(item.requester), "submitted": item.submitted_at or item.created_at, "status": item.get_status_display()} for item in pending_approvals[:5]],
        "recent_expenses": [{"pk": item.pk, "number": item.expense_number, "description": item.description, "category": categories.get(str(item.category_id), "Unassigned"), "date": item.expense_date, "amount": _money(item.amount), "approval": item.get_approval_status_display(), "record_status": item.record_status} for item in recent_expenses],
        "reminder_counts": {status: sum(item.status == status for item in reminders) for status in (PaymentReminder.Status.DRAFT, PaymentReminder.Status.SENT, PaymentReminder.Status.FAILED, PaymentReminder.Status.CANCELLED)},
        "recent_reminders": [{"pk": item.pk, "number": item.reminder_number, "invoice": item.invoice_reference, "date": item.reminder_date, "status": item.status, "status_label": item.get_status_display()} for item in recent_reminders],
        "important_notifications": important_notifications,
        "unread_dashboard_notifications": sum(not item["is_read"] for item in important_notifications),
        "payables": {"total": _money(payable_total), "paid": _money(payable_paid), "outstanding": _money(payable_remaining), "overdue": _money(overdue_payable_amount), "open_bills": sum(item.remaining_amount > ZERO for item in active_bills), "overdue_bills": len(overdue_bills), "settled_percent": _percent(payable_paid, payable_total)},
        "recent_supplier_payments": [{"number": item.payment_number, "supplier": suppliers.get(str(item.supplier_id), "Supplier"), "date": item.payment_date, "amount": _money(item.amount), "method": item.get_payment_method_display()} for item in recent_supplier_payments],
        "report_counts": report_counts, "report_total": len(readiness["catalog"]["reports"]),
        "quick_actions": quick_actions,
        "can_create_expense": _can(user, "payables.add_expense"),
        "can_view_approvals": _can(user, "payables.view_approvalrequest"),
    }

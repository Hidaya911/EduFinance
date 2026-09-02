# myproject/views.py
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from payables.models import ApprovalRequest, Discount, Expense, Scholarship, SupplierBill
from payables.views import get_school_currency
from school_config.models import School


ZERO = Decimal("0.00")


def base_preview_view(request):
    return render(request, 'accounts/preview.html')


def _money(value):
    return f"{value or ZERO:,.2f}"


def _percentage(numerator, denominator):
    if not denominator:
        return 0
    return min(100, round((numerator / denominator) * 100))


def dashboard_view(request):
    school = School.objects.first()
    currency_code = get_school_currency()
    academic_year = (
        school.current_academic_year.strip()
        if school and school.current_academic_year
        else "Not configured"
    )

    active_expenses = Expense.objects.filter(record_status=Expense.RecordStatus.ACTIVE)
    total_expenses = active_expenses.aggregate(total=Sum("amount"))["total"] or ZERO

    active_bills = SupplierBill.objects.exclude(status=SupplierBill.Status.CANCELLED)
    bill_totals = active_bills.aggregate(
        total=Sum("total_amount"),
        paid=Sum("amount_paid"),
        remaining=Sum("remaining_amount"),
    )
    payable_total = bill_totals["total"] or ZERO
    payable_paid = bill_totals["paid"] or ZERO
    payable_remaining = bill_totals["remaining"] or ZERO
    overdue_payables = (
        active_bills.filter(status=SupplierBill.Status.OVERDUE)
        .aggregate(total=Sum("remaining_amount"))["total"]
        or ZERO
    )

    bill_statuses = [
        (SupplierBill.Status.UNPAID, "Unpaid", "#f59e0b"),
        (SupplierBill.Status.PARTIALLY_PAID, "Partially paid", "#2563eb"),
        (SupplierBill.Status.PAID, "Paid", "#10b981"),
        (SupplierBill.Status.OVERDUE, "Overdue", "#ef4444"),
    ]
    bill_breakdown = []
    bill_count = active_bills.count()
    cursor = 0
    ring_segments = []
    for status, label, color in bill_statuses:
        count = active_bills.filter(status=status).count()
        percent = _percentage(Decimal(count), Decimal(bill_count))
        bill_breakdown.append(
            {"label": label, "count": count, "percent": percent, "color": color}
        )
        if count:
            end = cursor + (count / bill_count * 100)
            ring_segments.append(f"{color} {cursor:.2f}% {end:.2f}%")
            cursor = end

    pending_scholarships = Scholarship.objects.filter(
        status=Scholarship.Status.PENDING_APPROVAL,
    ).count()
    overdue_bill_count = active_bills.filter(status=SupplierBill.Status.OVERDUE).count()

    attention_items = []
    if request.user.is_staff or request.user.is_superuser:
        pending_approvals = ApprovalRequest.objects.filter(
            status__in=[
                ApprovalRequest.Status.REQUESTED,
                ApprovalRequest.Status.PENDING,
            ],
        ).count()
        attention_items.append(
            {
                "icon": "bi-check2-square",
                "tone": "amber",
                "title": "Approvals awaiting review",
                "count": pending_approvals,
                "detail": "Requested or pending financial approvals",
                "url": reverse("payables:approval_list"),
            }
        )
    attention_items.extend(
        [
            {
                "icon": "bi-mortarboard",
                "tone": "blue",
                "title": "Scholarships pending approval",
                "count": pending_scholarships,
                "detail": "Scholarship records awaiting a decision",
                "url": reverse("payables:scholarship_list"),
            },
            {
                "icon": "bi-receipt-cutoff",
                "tone": "red",
                "title": "Overdue supplier bills",
                "count": overdue_bill_count,
                "detail": "Open bills currently marked overdue",
                "url": reverse("payables:supplier_bill_list"),
            },
        ]
    )

    financial_pulse = []
    if request.user.is_staff or request.user.is_superuser:
        financial_pulse.append(
            {
                "label": "Approvals waiting",
                "value": str(pending_approvals),
                "icon": "bi-check2-square",
                "url": reverse("payables:approval_list"),
            }
        )
    financial_pulse.extend(
        [
            {
                "label": "Scholarships pending",
                "value": str(pending_scholarships),
                "icon": "bi-mortarboard",
                "url": reverse("payables:scholarship_list"),
            },
            {
                "label": "Open payables",
                "value": f"{currency_code} {_money(payable_remaining)}",
                "icon": "bi-receipt",
                "url": reverse("payables:supplier_bill_list"),
            },
        ]
    )

    activities = []
    activity_sources = (
        (
            active_expenses.order_by("-updated_at")[:3],
            lambda item: {
                "icon": "bi-wallet2",
                "tone": "red",
                "title": "Expense recorded",
                "reference": item.expense_number,
                "value": f"{currency_code} {_money(item.amount)}",
                "status": item.get_approval_status_display(),
                "url": reverse("payables:expense_detail", args=[item.pk]),
            },
        ),
        (
            SupplierBill.objects.order_by("-updated_at")[:3],
            lambda item: {
                "icon": "bi-receipt",
                "tone": "amber",
                "title": "Supplier bill updated",
                "reference": item.bill_number,
                "value": f"{currency_code} {_money(item.total_amount)}",
                "status": item.get_status_display(),
                "url": reverse("payables:supplier_bill_detail", args=[item.pk]),
            },
        ),
        (
            Scholarship.objects.order_by("-updated_at")[:3],
            lambda item: {
                "icon": "bi-mortarboard",
                "tone": "blue",
                "title": item.scholarship_name,
                "reference": item.scholarship_number,
                "value": (
                    f"{item.value}%"
                    if item.value_type == Scholarship.ValueType.PERCENTAGE
                    else f"{currency_code} {_money(item.value)}"
                ),
                "status": item.get_status_display(),
                "url": reverse("payables:scholarship_detail", args=[item.pk]),
            },
        ),
        (
            Discount.objects.order_by("-updated_at")[:3],
            lambda item: {
                "icon": "bi-tag",
                "tone": "green",
                "title": "Discount updated",
                "reference": item.discount_number,
                "value": (
                    f"{item.value}%"
                    if item.value_type == Discount.ValueType.PERCENTAGE
                    else f"{currency_code} {_money(item.value)}"
                ),
                "status": item.get_status_display(),
                "url": reverse("payables:discount_detail", args=[item.pk]),
            },
        ),
    )
    for records, serialize in activity_sources:
        for record in records:
            activity = serialize(record)
            activity["timestamp"] = record.updated_at
            activities.append(activity)
    activities.sort(key=lambda activity: activity["timestamp"], reverse=True)

    if request.user.is_authenticated:
        display_name = request.user.get_full_name().strip()
        if not display_name:
            display_name = request.user.get_username()
    else:
        display_name = "there"
    hour = timezone.localtime().hour

    context = {
        "display_name": display_name,
        "greeting": "Good morning" if hour < 12 else (
            "Good afternoon" if hour < 18 else "Good evening"
        ),
        "academic_year": academic_year,
        "currency_code": currency_code,
        "kpis": [
            {"label": "Expected revenue", "value": "0.00", "icon": "bi-graph-up-arrow", "tone": "blue", "detail": "Student billing is not implemented"},
            {"label": "Total collected", "value": "0.00", "icon": "bi-bank", "tone": "green", "detail": "Collection data is not available"},
            {"label": "Outstanding balance", "value": "0.00", "icon": "bi-hourglass-split", "tone": "amber", "detail": "No student receivables model"},
            {"label": "Overdue amount", "value": "0.00", "icon": "bi-exclamation-circle", "tone": "red", "detail": "No student invoice due dates"},
            {"label": "Total expenses", "value": _money(total_expenses), "icon": "bi-wallet2", "tone": "violet", "detail": "Active expense records"},
        ],
        "financial_health": [
            {"label": "Payables settled", "value": _percentage(payable_paid, payable_total), "detail": f"{currency_code} {_money(payable_paid)} paid"},
            {"label": "Open payables", "value": _percentage(payable_remaining, payable_total), "detail": f"{currency_code} {_money(payable_remaining)} outstanding"},
            {"label": "Overdue risk", "value": _percentage(overdue_payables, payable_remaining), "detail": f"{currency_code} {_money(overdue_payables)} overdue"},
        ],
        "health_score": _percentage(payable_paid, payable_total),
        "has_payable_data": bool(payable_total),
        "financial_pulse": financial_pulse,
        "attention_items": attention_items,
        "bill_breakdown": bill_breakdown,
        "bill_count": bill_count,
        "bill_ring": ", ".join(ring_segments) if ring_segments else "#e2e8f0 0 100%",
        "activities": activities[:7],
    }
    return render(request, "dashboard.html", context)

"""Read-only student finance definitions shared by dashboard and reports.

Issued invoices (unpaid/partially_paid/paid/overdue) are obligations;
draft and void invoices are not. Completed payments are gross collections,
dated by payment_date. Invoice.balance is authoritative and is never reduced
again for text-reference discounts/scholarships. Refund processing is blocked
by the existing workflow pending verified ledger linkage; refund workflow
values are reported separately, never treated as payment reversals here.
No status refresh/save is performed while reading financial data.
"""

from collections import defaultdict
from decimal import Decimal

from django.utils import timezone

from accounts.core.models import AcademicYear
from billing.models import Invoice, Payment, Installment
from school_config.models import School, Grade, SchoolClass
from .overdue_services import build_overdue_row, summarize_overdue_rows

ZERO = Decimal("0.00")
VALID_INVOICE_STATUSES = (
    Invoice.STATUS_UNPAID, Invoice.STATUS_PARTIAL,
    Invoice.STATUS_PAID, Invoice.STATUS_OVERDUE,
)


def school_context(school):
    year = AcademicYear.objects.filter(is_current=True).order_by("-start_date", "pk").first()
    return {
        "currency_code": school.default_currency if school else School._meta.get_field("default_currency").default,
        "academic_year": year.name if year else (school.current_academic_year.strip() if school and school.current_academic_year else "Not configured"),
    }


def valid_invoices(school):
    return Invoice.objects.filter(school=school, status__in=VALID_INVOICE_STATUSES)


def valid_payments(school):
    return Payment.objects.filter(school=school, status="completed")


def outstanding(invoice):
    return max(invoice.balance, ZERO)


def summarize_student_finance(invoices, payments, today=None):
    today = today or timezone.localdate()
    invoices, payments = list(invoices), list(payments)
    expected = sum((x.total_amount for x in invoices), ZERO)
    collected = sum((x.amount for x in payments), ZERO)
    monthly = defaultdict(Decimal)
    for payment in payments:
        monthly[payment.payment_date.strftime("%Y-%m")] += payment.amount
    return {
        "expected": expected, "collected": collected,
        "outstanding": sum((outstanding(x) for x in invoices), ZERO),
        "collection_percent": collected / expected * 100 if expected > ZERO else None,
        "monthly_revenue": dict(monthly),
        "month_revenue": monthly[today.strftime("%Y-%m")],
    }


def invoice_overdue_rows(invoices, today=None, grades=None, classes=None):
    grades, classes = grades or {}, classes or {}
    rows = []
    for invoice in invoices:
        row = build_overdue_row(
            source_id=invoice.pk, invoice_number=invoice.invoice_number,
            student_reference=invoice.student.student_number,
            student_name=invoice.student.full_name,
            academic_year=invoice.academic_year.name,
            grade=grades.get(str(invoice.enrollment.grade_id), ""),
            class_name=classes.get(str(invoice.enrollment.classroom_id), ""),
            due_date=invoice.due_date, outstanding_amount=outstanding(invoice),
            source_status=invoice.status, as_of_date=today,
        )
        if row:
            rows.append(row)
    return rows


def installment_remaining(installment):
    return max(installment.amount - installment.paid_amount, ZERO)


def installment_status(installment, today):
    # Mirror the model's status precedence without its database-writing refresh.
    if installment_remaining(installment) == ZERO:
        return "paid"
    if installment.paid_amount > ZERO:
        return "partially_paid"
    return "overdue" if installment.due_date < today else "pending"


def get_student_finance_data(school=None, today=None):
    today = today or timezone.localdate()
    school = school or School.objects.first()
    invoices = list(valid_invoices(school).select_related("student", "enrollment", "academic_year"))
    payments = list(valid_payments(school).select_related("student").prefetch_related("receipt").order_by("-payment_date", "-created_at", "-pk"))
    installments = list(Installment.objects.filter(
        plan__school=school, plan__status__in=("active", "completed"),
        plan__invoice__status__in=VALID_INVOICE_STATUSES,
    ).select_related("plan__student", "plan__invoice", "plan__academic_year").order_by("due_date", "installment_number", "pk"))
    grades = {str(x.pk): x.name for x in Grade.objects.all()}
    classes = {str(x.pk): x.name for x in SchoolClass.objects.all()}
    overdue_rows = invoice_overdue_rows(invoices, today, grades, classes)
    upcoming = [x for x in installments if x.plan.status == "active" and x.status != "paid" and x.due_date >= today and installment_remaining(x) > ZERO and outstanding(x.plan.invoice) > ZERO]
    return {
        **summarize_student_finance(invoices, payments, today),
        "invoices": invoices, "payments": payments, "installments": installments,
        "overdue_rows": overdue_rows, "overdue_summary": summarize_overdue_rows(overdue_rows),
        "recent_payments": payments[:5], "upcoming_installments": upcoming[:5],
        "grades": grades, "classes": classes,
    }


def get_student_invoice_overdue_rows():
    school = School.objects.first()
    invoices = valid_invoices(school).select_related("student", "enrollment", "academic_year")
    return invoice_overdue_rows(
        invoices, timezone.localdate(),
        {str(x.pk): x.name for x in Grade.objects.all()},
        {str(x.pk): x.name for x in SchoolClass.objects.all()},
    )


def issued_receipt(payment):
    receipt = getattr(payment, "receipt", None)
    return receipt.receipt_number if receipt and receipt.status == "issued" else ""


def reminder_invoice(reminder, invoices_by_number):
    """Resolve an exact invoice number only when its student also matches."""
    invoice = invoices_by_number.get(reminder.invoice_reference.strip())
    if invoice and str(invoice.student_id) == str(reminder.student_id):
        return invoice
    return None

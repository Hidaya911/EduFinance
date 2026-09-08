"""Read-only report calculations for the EduFinance Reports workspace."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from school_config.models import School

from .models import (
    Discount,
    Expense,
    ExpenseCategory,
    FinancialAssistanceRequest,
    Refund,
    Scholarship,
    Supplier,
    SupplierBill,
    SupplierPayment,
)
from .student_finance_services import (
    get_student_finance_data, school_context, summarize_student_finance,
    invoice_overdue_rows, outstanding, issued_receipt,
    installment_remaining, installment_status,
)
from .overdue_services import AGING_LABELS, summarize_overdue_rows


ZERO = Decimal("0.00")


REPORT_DEFINITIONS = (
    {"id": "REP-001", "slug": "fee-collection", "title": "Fee Collection Report", "category": "Revenue & Collections", "status": "ready", "description": "Expected, collected, remaining, and collection performance from student invoices and payments.", "dependency": ""},
    {"id": "REP-002", "slug": "student-balance", "title": "Student Balance Report", "category": "Student Receivables", "status": "ready", "description": "Student-level invoiced, paid, outstanding, and overdue balances.", "dependency": ""},
    {"id": "REP-003", "slug": "payment-report", "title": "Payment Report", "category": "Revenue & Collections", "status": "ready", "description": "Traceable student payment register with method, date, and receipt context.", "dependency": ""},
    {"id": "REP-004", "slug": "daily-collection", "title": "Daily Collection Report", "category": "Revenue & Collections", "status": "ready", "description": "Daily student collections and transaction volume.", "dependency": ""},
    {"id": "REP-005", "slug": "monthly-revenue", "title": "Monthly Revenue Report", "category": "Revenue & Collections", "status": "ready", "description": "Monthly gross student collections and collection trends.", "dependency": ""},
    {"id": "REP-006", "slug": "expense-report", "title": "Expense Report", "category": "Operations & Payables", "status": "ready", "description": "Active and voided operating expenses with approval and payment context.", "dependency": ""},
    {"id": "REP-007", "slug": "revenue-vs-expense", "title": "Revenue vs Expense Report", "category": "Executive Analysis", "status": "ready", "description": "Completed student collections compared with active operating expenses.", "dependency": ""},
    {"id": "REP-008", "slug": "scholarship-report", "title": "Scholarship Report", "category": "Financial Adjustments", "status": "ready", "description": "Scholarship portfolio by lifecycle, academic year, and value type.", "dependency": ""},
    {"id": "REP-009", "slug": "discount-report", "title": "Discount Report", "category": "Financial Adjustments", "status": "ready", "description": "Discount register with fixed and percentage values reported separately.", "dependency": ""},
    {"id": "REP-010", "slug": "installment-report", "title": "Installment Report", "category": "Student Receivables", "status": "ready", "description": "Installment schedules, due dates, payments, and remaining balances.", "dependency": ""},
    {"id": "REP-011", "slug": "overdue-report", "title": "Overdue Payment Report", "category": "Student Receivables", "status": "ready", "description": "Student receivables overdue under the official aging rules.", "dependency": ""},
    {"id": "REP-012", "slug": "refund-report", "title": "Refund Report", "category": "Financial Adjustments", "status": "partial", "description": "Real refund requests and workflow values without claiming payment-ledger reversal.", "dependency": "Validated originating-payment linkage and refundable-balance accounting"},
    {"id": "REP-013", "slug": "supplier-balance", "title": "Supplier Balance Report", "category": "Operations & Payables", "status": "ready", "description": "Supplier billed, paid, and outstanding positions excluding cancelled and voided activity.", "dependency": ""},
    {"id": "REP-014", "slug": "payment-method", "title": "Payment Method Report", "category": "Revenue & Collections", "status": "ready", "description": "Student collections grouped by payment method.", "dependency": ""},
    {"id": "REP-015", "slug": "financial-assistance", "title": "Financial Assistance Report", "category": "Financial Adjustments", "status": "ready", "description": "Assistance cases, documentation, academic-year context, and approval lifecycle.", "dependency": ""},
)


def get_report_definition(slug):
    return next((item for item in REPORT_DEFINITIONS if item["slug"] == slug), None)


def get_reports_catalog():
    categories = []
    for name in ("Revenue & Collections", "Student Receivables", "Financial Adjustments", "Operations & Payables", "Executive Analysis"):
        categories.append({"name": name, "reports": [dict(item) for item in REPORT_DEFINITIONS if item["category"] == name]})
    counts = {key: sum(item["status"] == key for item in REPORT_DEFINITIONS) for key in ("ready", "partial", "integration_pending")}
    return {"reports": [dict(item) for item in REPORT_DEFINITIONS], "categories": categories, "counts": counts}


def get_school_context():
    return school_context(School.objects.first())


def _date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    except ValueError:
        return None


def _money(value, currency):
    return f"{currency} {(value or ZERO):,.2f}"


def _number(value):
    return f"{value or ZERO:,.2f}"


def _text(value):
    return str(value or "").strip()


def _matches(search, *values):
    return not search or search.lower() in " ".join(_text(value) for value in values).lower()


def _within(value, start, end):
    if hasattr(value, "date"):
        value = value.date()
    return bool(value) and (not start or value >= start) and (not end or value <= end)


def _choice_options(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _filter(name, label, value="", kind="select", options=None, placeholder=""):
    return {"name": name, "label": label, "value": value, "kind": kind, "options": options or [], "placeholder": placeholder}


def _row(values, export_values=None, status="", status_index=None):
    return {"cells": values, "export": export_values or values, "status": status, "status_index": status_index}


def _base_result(definition, filters, columns, rows, kpis, summary, export_enabled=True, note=""):
    return {"report": dict(definition), "filters": filters, "columns": columns, "rows": rows, "kpis": kpis, "summary": summary, "export_enabled": export_enabled, "note": note}


def summarize_expenses(records, today=None):
    """Return the shared active-expense and workflow summary."""
    records = list(records)
    today = today or timezone.localdate()
    active = [item for item in records if item.record_status == Expense.RecordStatus.ACTIVE]
    current_month = [item for item in active if item.expense_date.year == today.year and item.expense_date.month == today.month]
    return {
        "records": records,
        "active": active,
        "current_month": current_month,
        "active_total": sum((item.amount or ZERO for item in active), ZERO),
        "current_month_total": sum((item.amount or ZERO for item in current_month), ZERO),
        "pending_count": sum(item.approval_status == Expense.ApprovalStatus.PENDING for item in active),
        "approved_count": sum(item.approval_status == Expense.ApprovalStatus.APPROVED for item in active),
        "voided_count": sum(item.record_status == Expense.RecordStatus.VOIDED for item in records),
    }


def get_expense_report(params, currency):
    search, status = params.get("search", "").strip(), params.get("status", "").strip()
    category, supplier = params.get("category", "").strip(), params.get("supplier", "").strip()
    method, approval = params.get("payment_method", "").strip(), params.get("approval_status", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    records = list(Expense.objects.all())
    filtered = [item for item in records if _matches(search, item.expense_number, item.description, item.reference, item.category, item.supplier) and (not status or item.record_status == status) and (not category or str(item.category_id) == category) and (not supplier or str(item.supplier_id or "") == supplier) and (not method or item.payment_method == method) and (not approval or item.approval_status == approval) and _within(item.expense_date, start, end)]
    filtered.sort(key=lambda item: (item.expense_date, item.created_at), reverse=True)
    expense_summary = summarize_expenses(records)
    active = expense_summary["active"]
    rows = [_row([item.expense_number, item.expense_date.strftime("%d %b %Y"), str(item.category), str(item.supplier or "—"), item.description, item.get_payment_method_display(), item.get_approval_status_display(), item.get_record_status_display(), _money(item.amount, currency)], [item.expense_number, item.expense_date.isoformat(), str(item.category), str(item.supplier or ""), item.description, item.get_payment_method_display(), item.get_approval_status_display(), item.get_record_status_display(), _number(item.amount)], item.record_status, 7) for item in filtered]
    filters = [_filter("search", "Search", search, "search", placeholder="Number, description, reference, category or supplier"), _filter("date_from", "From", params.get("date_from", ""), "date"), _filter("date_to", "To", params.get("date_to", ""), "date"), _filter("category", "Category", category, options=[{"value": str(x.pk), "label": x.name} for x in ExpenseCategory.objects.order_by("name")]), _filter("supplier", "Supplier", supplier, options=[{"value": str(x.pk), "label": x.name} for x in Supplier.objects.order_by("name")]), _filter("payment_method", "Payment method", method, options=_choice_options(Expense.PaymentMethod.choices)), _filter("approval_status", "Approval", approval, options=_choice_options(Expense.ApprovalStatus.choices)), _filter("status", "Record status", status, options=_choice_options(Expense.RecordStatus.choices))]
    kpis = [{"label": "Active expense", "value": _money(expense_summary["active_total"], currency), "tone": "blue"}, {"label": "Active records", "value": len(active), "tone": "green"}, {"label": "Pending approval", "value": expense_summary["pending_count"], "tone": "amber"}, {"label": "Approved", "value": expense_summary["approved_count"], "tone": "green"}, {"label": "Voided", "value": expense_summary["voided_count"], "tone": "red"}]
    return _base_result(get_report_definition("expense-report"), filters, ["Expense", "Date", "Category", "Supplier", "Description", "Method", "Approval", "Status", f"Amount ({currency})"], rows, kpis, "Financial totals exclude voided expenses. The table may include voided records when requested by the status filter.")


def get_scholarship_report(params, currency):
    search, status = params.get("search", "").strip(), params.get("status", "").strip()
    value_type, year = params.get("value_type", "").strip(), params.get("academic_year", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    records = list(Scholarship.objects.all())
    filtered = [x for x in records if _matches(search, x.scholarship_number, x.scholarship_name, x.student_reference, x.provider, x.reason) and (not status or x.status == status) and (not value_type or x.value_type == value_type) and (not year or x.academic_year_reference == year) and _within(x.start_date, start, end)]
    filtered.sort(key=lambda x: (x.start_date, x.created_at), reverse=True)
    fixed = [x for x in records if x.value_type == Scholarship.ValueType.FIXED_AMOUNT and x.status != Scholarship.Status.CANCELLED]
    percentage = [x for x in records if x.value_type == Scholarship.ValueType.PERCENTAGE and x.status != Scholarship.Status.CANCELLED]
    rows = [_row([x.scholarship_number, x.scholarship_name, x.student_reference, x.academic_year_reference, x.provider or "—", x.get_value_type_display(), _money(x.value, currency) if x.value_type == Scholarship.ValueType.FIXED_AMOUNT else f"{x.value:,.2f}%", x.get_status_display(), x.start_date.strftime("%d %b %Y")], [x.scholarship_number, x.scholarship_name, x.student_reference, x.academic_year_reference, x.provider, x.get_value_type_display(), _number(x.value), x.get_status_display(), x.start_date.isoformat()], x.status, 7) for x in filtered]
    years = sorted({_text(x.academic_year_reference) for x in records if x.academic_year_reference}, reverse=True)
    filters = [_filter("search", "Search", search, "search", placeholder="Award, student, provider or reason"), _filter("date_from", "Starts from", params.get("date_from", ""), "date"), _filter("date_to", "Starts to", params.get("date_to", ""), "date"), _filter("academic_year", "Academic year", year, options=[{"value": x, "label": x} for x in years]), _filter("value_type", "Value type", value_type, options=_choice_options(Scholarship.ValueType.choices)), _filter("status", "Status", status, options=_choice_options(Scholarship.Status.choices))]
    kpis = [{"label": "Scholarships", "value": len(records), "tone": "blue"}, {"label": "Active fixed value", "value": _money(sum((x.value for x in fixed), ZERO), currency), "tone": "green"}, {"label": "Percentage awards", "value": len(percentage), "tone": "violet"}, {"label": "Pending approval", "value": sum(x.status == Scholarship.Status.PENDING_APPROVAL for x in records), "tone": "amber"}]
    return _base_result(get_report_definition("scholarship-report"), filters, ["Award", "Scholarship", "Student", "Academic year", "Provider", "Value type", "Value", "Status", "Start date"], rows, kpis, "Fixed monetary values and percentage awards are deliberately reported separately; percentages are never added to currency totals.")


def get_discount_report(params, currency):
    search, status = params.get("search", "").strip(), params.get("status", "").strip()
    value_type, discount_type = params.get("value_type", "").strip(), params.get("discount_type", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    records = list(Discount.objects.all())
    filtered = [x for x in records if _matches(search, x.discount_number, x.student_reference, x.invoice_reference, x.reason) and (not status or x.status == status) and (not value_type or x.value_type == value_type) and (not discount_type or x.discount_type == discount_type) and _within(x.discount_date, start, end)]
    filtered.sort(key=lambda x: (x.discount_date, x.created_at), reverse=True)
    fixed = [x for x in records if x.value_type == Discount.ValueType.FIXED_AMOUNT and x.status != Discount.Status.CANCELLED]
    percentage = [x for x in records if x.value_type == Discount.ValueType.PERCENTAGE and x.status != Discount.Status.CANCELLED]
    rows = [_row([x.discount_number, x.discount_date.strftime("%d %b %Y"), x.student_reference, x.invoice_reference, x.get_discount_type_display(), x.get_value_type_display(), _money(x.value, currency) if x.value_type == Discount.ValueType.FIXED_AMOUNT else f"{x.value:,.2f}%", x.get_status_display()], [x.discount_number, x.discount_date.isoformat(), x.student_reference, x.invoice_reference, x.get_discount_type_display(), x.get_value_type_display(), _number(x.value), x.get_status_display()], x.status, 7) for x in filtered]
    filters = [_filter("search", "Search", search, "search", placeholder="Discount, student, invoice or reason"), _filter("date_from", "From", params.get("date_from", ""), "date"), _filter("date_to", "To", params.get("date_to", ""), "date"), _filter("discount_type", "Discount type", discount_type, options=_choice_options(Discount.DiscountType.choices)), _filter("value_type", "Value type", value_type, options=_choice_options(Discount.ValueType.choices)), _filter("status", "Status", status, options=_choice_options(Discount.Status.choices))]
    kpis = [{"label": "Discounts", "value": len(records), "tone": "blue"}, {"label": "Active fixed value", "value": _money(sum((x.value for x in fixed), ZERO), currency), "tone": "green"}, {"label": "Percentage discounts", "value": len(percentage), "tone": "violet"}, {"label": "Pending approval", "value": sum(x.status == Discount.Status.PENDING_APPROVAL for x in records), "tone": "amber"}]
    return _base_result(get_report_definition("discount-report"), filters, ["Discount", "Date", "Student", "Invoice reference", "Type", "Value type", "Value", "Status"], rows, kpis, "Fixed monetary values and percentages remain separate because no applied invoice amount is available.")


def get_refund_report(params, currency):
    search, status, method = params.get("search", "").strip(), params.get("status", "").strip(), params.get("refund_method", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    records = list(Refund.objects.all())
    filtered = [x for x in records if _matches(search, x.refund_number, x.student_reference, x.original_payment_reference, x.reason) and (not status or x.status == status) and (not method or x.refund_method == method) and _within(x.requested_at, start, end)]
    filtered.sort(key=lambda x: (x.requested_at, x.created_at), reverse=True)
    active = [x for x in records if x.status != Refund.Status.CANCELLED]
    processed = [x for x in records if x.status == Refund.Status.PROCESSED]
    rows = [_row([x.refund_number, timezone.localtime(x.requested_at).strftime("%d %b %Y"), x.student_reference, x.original_payment_reference, x.get_refund_method_display(), _money(x.amount, currency), x.get_status_display(), x.reason], [x.refund_number, timezone.localtime(x.requested_at).date().isoformat(), x.student_reference, x.original_payment_reference, x.get_refund_method_display(), _number(x.amount), x.get_status_display(), x.reason], x.status, 6) for x in filtered]
    filters = [_filter("search", "Search", search, "search", placeholder="Refund, student, payment reference or reason"), _filter("date_from", "Requested from", params.get("date_from", ""), "date"), _filter("date_to", "Requested to", params.get("date_to", ""), "date"), _filter("refund_method", "Method", method, options=_choice_options(Refund.RefundMethod.choices)), _filter("status", "Status", status, options=_choice_options(Refund.Status.choices))]
    kpis = [{"label": "Refund requests", "value": len(records), "tone": "blue"}, {"label": "Active requested value", "value": _money(sum((x.amount for x in active), ZERO), currency), "tone": "amber"}, {"label": "Processed records", "value": len(processed), "tone": "green"}, {"label": "Processed value", "value": _money(sum((x.amount for x in processed), ZERO), currency), "tone": "violet"}]
    return _base_result(get_report_definition("refund-report"), filters, ["Refund", "Requested", "Student reference", "Payment reference", "Method", f"Amount ({currency})", "Workflow status", "Reason"], rows, kpis, "These are real refund workflow records. Payment references are currently text snapshots, so this report does not claim a verified student-ledger reversal.", note="The existing refund workflow still blocks processing until originating-payment linkage and the remaining refundable balance are validated.")


def get_supplier_balance_report(params, currency):
    search, supplier_id, bill_status = params.get("search", "").strip(), params.get("supplier", "").strip(), params.get("status", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    suppliers, bills, payments = list(Supplier.objects.all()), list(SupplierBill.objects.all()), list(SupplierPayment.objects.all())
    by_supplier = defaultdict(lambda: {"bills": 0, "billed": ZERO, "paid_on_bills": ZERO, "outstanding": ZERO, "posted_payments": ZERO})
    for bill in bills:
        if bill.status == SupplierBill.Status.CANCELLED or (bill_status and bill.status != bill_status) or not _within(bill.bill_date, start, end):
            continue
        data = by_supplier[str(bill.supplier_id)]; data["bills"] += 1; data["billed"] += bill.total_amount or ZERO; data["paid_on_bills"] += bill.amount_paid or ZERO; data["outstanding"] += bill.remaining_amount or ZERO
    for payment in payments:
        if payment.status == SupplierPayment.Status.POSTED and _within(payment.payment_date, start, end):
            by_supplier[str(payment.supplier_id)]["posted_payments"] += payment.amount or ZERO
    rows = []
    for supplier in suppliers:
        data = by_supplier[str(supplier.pk)]
        if (supplier_id and str(supplier.pk) != supplier_id) or not _matches(search, supplier.name, supplier.contact_person, supplier.email, supplier.tax_number):
            continue
        if (start or end or bill_status) and not data["bills"]:
            continue
        rows.append(_row([supplier.name, "Active" if supplier.is_active else "Inactive", data["bills"], _money(data["billed"], currency), _money(data["paid_on_bills"], currency), _money(data["posted_payments"], currency), _money(data["outstanding"], currency)], [supplier.name, "Active" if supplier.is_active else "Inactive", data["bills"], _number(data["billed"]), _number(data["paid_on_bills"]), _number(data["posted_payments"]), _number(data["outstanding"])], "active" if supplier.is_active else "inactive", 1))
    rows.sort(key=lambda row: Decimal(row["export"][-1].replace(",", "")), reverse=True)
    active_bills = [x for x in bills if x.status != SupplierBill.Status.CANCELLED]
    posted = [x for x in payments if x.status == SupplierPayment.Status.POSTED]
    bill_status_choices = [choice for choice in SupplierBill.Status.choices if choice[0] != SupplierBill.Status.CANCELLED]
    filters = [_filter("search", "Search", search, "search", placeholder="Supplier, contact, email or tax number"), _filter("date_from", "Bill/payment from", params.get("date_from", ""), "date"), _filter("date_to", "Bill/payment to", params.get("date_to", ""), "date"), _filter("supplier", "Supplier", supplier_id, options=[{"value": str(x.pk), "label": x.name} for x in sorted(suppliers, key=lambda x: x.name.lower())]), _filter("status", "Bill status", bill_status, options=_choice_options(bill_status_choices))]
    kpis = [{"label": "Active billed", "value": _money(sum((x.total_amount for x in active_bills), ZERO), currency), "tone": "blue"}, {"label": "Outstanding", "value": _money(sum((x.remaining_amount for x in active_bills), ZERO), currency), "tone": "amber"}, {"label": "Posted payments", "value": _money(sum((x.amount for x in posted), ZERO), currency), "tone": "green"}, {"label": "Open suppliers", "value": sum(by_supplier[str(x.pk)]["outstanding"] > ZERO for x in suppliers), "tone": "violet"}]
    return _base_result(get_report_definition("supplier-balance"), filters, ["Supplier", "Supplier status", "Active bills", f"Billed ({currency})", f"Bill paid ({currency})", f"Posted payments ({currency})", f"Outstanding ({currency})"], rows, kpis, "Cancelled bills and voided supplier payments are excluded. Bill balances remain the authoritative payable position; posted payment totals provide an independent transaction view.")


def get_financial_assistance_report(params, currency):
    search, status, year = params.get("search", "").strip(), params.get("status", "").strip(), params.get("academic_year", "").strip()
    documentation = params.get("documentation", "").strip()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    records = list(FinancialAssistanceRequest.objects.all())
    filtered = [x for x in records if _matches(search, x.assistance_number, x.student_reference, x.academic_year_reference, x.reason) and (not status or x.status == status) and (not year or x.academic_year_reference == year) and (not documentation or (documentation == "attached") == bool(x.supporting_document)) and _within(x.created_at, start, end)]
    filtered.sort(key=lambda x: x.created_at, reverse=True)
    rows = [_row([x.assistance_number, x.student_reference, x.academic_year_reference, x.get_status_display(), "Attached" if x.supporting_document else "Not attached", timezone.localtime(x.created_at).strftime("%d %b %Y"), x.reason], [x.assistance_number, x.student_reference, x.academic_year_reference, x.get_status_display(), "Attached" if x.supporting_document else "Not attached", timezone.localtime(x.created_at).date().isoformat(), x.reason], x.status, 3) for x in filtered]
    years = sorted({_text(x.academic_year_reference) for x in records if x.academic_year_reference}, reverse=True)
    filters = [_filter("search", "Search", search, "search", placeholder="Case, student, academic year or reason"), _filter("date_from", "Created from", params.get("date_from", ""), "date"), _filter("date_to", "Created to", params.get("date_to", ""), "date"), _filter("academic_year", "Academic year", year, options=[{"value": x, "label": x} for x in years]), _filter("documentation", "Documentation", documentation, options=[{"value": "attached", "label": "Attached"}, {"value": "missing", "label": "Not attached"}]), _filter("status", "Status", status, options=_choice_options(FinancialAssistanceRequest.Status.choices))]
    kpis = [{"label": "Requests", "value": len(records), "tone": "blue"}, {"label": "Under review", "value": sum(x.status == FinancialAssistanceRequest.Status.UNDER_REVIEW for x in records), "tone": "amber"}, {"label": "Approved", "value": sum(x.status == FinancialAssistanceRequest.Status.APPROVED for x in records), "tone": "green"}, {"label": "Documented", "value": sum(bool(x.supporting_document) for x in records), "tone": "violet"}]
    return _base_result(get_report_definition("financial-assistance"), filters, ["Case", "Student reference", "Academic year", "Status", "Documentation", "Created", "Reason"], rows, kpis, "Financial assistance has no BRD-defined amount. This report intentionally measures requests, evidence, and lifecycle only.")


STUDENT_REPORTS = {
    "fee-collection", "student-balance", "payment-report", "daily-collection",
    "monthly-revenue", "revenue-vs-expense", "installment-report",
    "overdue-report", "payment-method",
}


def get_student_report(slug, params, currency):
    """Filter real source records, then summarize the same definitions as the dashboard."""
    data = get_student_finance_data()
    today = timezone.localdate()
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    search = params.get("search", "").strip()
    filters = [_filter("date_from", "From", params.get("date_from", ""), "date"),
               _filter("date_to", "To", params.get("date_to", ""), "date")]
    if slug != "revenue-vs-expense":
        filters.insert(0, _filter("search", "Student / reference", search, "search"))
    invoices = [x for x in data["invoices"] if
                _matches(search, x.invoice_number, x.student.full_name, x.student.student_number)
                and _within(timezone.localtime(x.created_at).date(), start, end)]
    payments = [x for x in data["payments"] if
                _matches(search, x.payment_number, issued_receipt(x), x.student.full_name, x.student.student_number)
                and _within(x.payment_date, start, end)]
    rows, kpis = [], []
    summary = "Completed payments are gross collections by payment date. Refund workflow values remain separate. Totals cover the filtered records across academic years."

    def money_kpi(label, value, tone="blue"):
        return {"label": label, "value": _money(value, currency), "tone": tone}

    def financial_row(labels, amounts):
        return _row(labels + [_money(x, currency) for x in amounts],
                    labels + [_number(x) for x in amounts])

    if slug in ("fee-collection", "student-balance"):
        # Date filters deliberately operate on each ledger's own transaction date.
        totals = summarize_student_finance(invoices, payments, today)
        overdue = invoice_overdue_rows(invoices, today)
        overdue_by_student = defaultdict(Decimal)
        for row in overdue:
            overdue_by_student[row["student_reference"]] += row["outstanding_amount"]
        positions = {}
        for item in invoices + payments:
            positions.setdefault(str(item.student_id), {"student": item.student, "invoices": [], "payments": []})
        for item in invoices:
            positions[str(item.student_id)]["invoices"].append(item)
        for item in payments:
            positions[str(item.student_id)]["payments"].append(item)
        for position in sorted(positions.values(), key=lambda x: x["student"].full_name):
            student = position["student"]
            values = summarize_student_finance(position["invoices"], position["payments"], today)
            years = ", ".join(sorted({x.academic_year.name for x in position["invoices"]}))
            rows.append(financial_row([student.student_number, student.full_name, years],
                        [values["expected"], values["collected"], values["outstanding"], overdue_by_student[student.student_number]]))
        columns = ["Student number", "Student", "Invoice academic years", "Invoiced", "Collected", "Outstanding", "Overdue"]
        kpis = [money_kpi("Expected revenue", totals["expected"]), money_kpi("Total collected", totals["collected"], "green"),
                money_kpi("Outstanding", totals["outstanding"], "amber"),
                {"label": "Collection percentage", "value": f'{totals["collection_percent"]:,.2f}%' if totals["collection_percent"] is not None else "Not applicable", "tone": "blue"}]
        summary += " Invoice dates use local created_at; payment dates use payment_date. Outstanding is the current canonical balance of the selected invoices, not a reconstructed historical balance. No discount or scholarship is subtracted again."
    elif slug == "payment-report":
        method = params.get("payment_method", "").strip()
        payments = [x for x in payments if not method or x.payment_method == method]
        from billing.models import Payment
        filters.append(_filter("payment_method", "Method", method, options=_choice_options(Payment.METHOD_CHOICES)))
        columns = ["Payment", "Student number", "Student", "Date", "Method", "Receipt", "Status", f"Amount ({currency})"]
        for x in payments:
            rows.append(financial_row([x.payment_number, x.student.student_number, x.student.full_name,
                        x.payment_date.isoformat(), x.get_payment_method_display(), issued_receipt(x), x.get_status_display()], [x.amount]))
        kpis = [money_kpi("Total collected", summarize_student_finance([], payments, today)["collected"], "green"),
                {"label": "Payments", "value": len(payments), "tone": "blue"}]
    elif slug in ("daily-collection", "monthly-revenue", "payment-method"):
        groups = defaultdict(lambda: {"amount": ZERO, "count": 0})
        for x in payments:
            key = x.payment_date.isoformat() if slug == "daily-collection" else (x.payment_date.strftime("%Y-%m") if slug == "monthly-revenue" else x.get_payment_method_display())
            groups[key]["amount"] += x.amount
            groups[key]["count"] += 1
        columns = ["Day" if slug == "daily-collection" else "Month" if slug == "monthly-revenue" else "Method", "Payments", f"Collected ({currency})"]
        rows = [financial_row([key, value["count"]], [value["amount"]]) for key, value in sorted(groups.items())]
        kpis = [money_kpi("Total collected", summarize_student_finance([], payments, today)["collected"], "green")]
    elif slug == "installment-report":
        selected = [x for x in data["installments"] if _within(x.due_date, start, end) and
                    _matches(search, x.plan.student.full_name, x.plan.student.student_number, x.plan.invoice.invoice_number)]
        columns = ["Student", "Invoice", "Academic year", "Installment", "Due date", "Status", "Scheduled", "Paid", "Remaining"]
        for x in selected:
            rows.append(financial_row([x.plan.student.full_name, x.plan.invoice.invoice_number, x.plan.academic_year.name,
                        x.installment_number, x.due_date.isoformat(), dict(x.STATUS_CHOICES)[installment_status(x, today)]],
                        [x.amount, x.paid_amount, installment_remaining(x)]))
        kpis = [money_kpi("Scheduled", sum((x.amount for x in selected), ZERO)),
                money_kpi("Remaining", sum((installment_remaining(x) for x in selected), ZERO), "amber")]
        summary = "Due-date filters; active and completed plans on issued invoices only. Cancelled plans and draft/void invoices are excluded. Remaining is max(amount - paid_amount, 0); schedules are not added to invoice obligations."
    elif slug == "overdue-report":
        aging = params.get("aging", "").strip()
        filters.append(_filter("aging", "Aging", aging, options=_choice_options(AGING_LABELS.items())))
        selected = [x for x in data["overdue_rows"] if _within(x["due_date"], start, end) and
                    _matches(search, x["invoice_number"], x["student_reference"], x["student_name"]) and
                    (not aging or x["aging_bucket"] == aging)]
        selected.sort(key=lambda x: x["days_overdue"], reverse=True)
        columns = ["Invoice", "Student number", "Student", "Academic year", "Grade", "Class", "Due date", "Days overdue", "Aging", "Outstanding"]
        rows = [financial_row([x["invoice_number"], x["student_reference"], x["student_name"], x["academic_year"],
                x["grade"], x["class_name"], x["due_date"].isoformat(), x["days_overdue"], x["aging_label"]],
                [x["outstanding_amount"]]) for x in selected]
        totals = summarize_overdue_rows(selected)
        kpis = [money_kpi("Overdue", totals["total_overdue_amount"], "red"),
                {"label": "Invoices", "value": totals["overdue_invoice_count"], "tone": "amber"},
                {"label": "Students", "value": totals["overdue_student_count"], "tone": "blue"}]
        summary = "Due date < today and canonical outstanding balance > 0. Uses the shared overdue service and its four aging bands; filters use invoice due dates."
    else:  # revenue-vs-expense
        # Search is not exposed here: both sides must use the same date scope.
        payments = [x for x in data["payments"] if _within(x.payment_date, start, end)]
        expenses = summarize_expenses([x for x in Expense.objects.all() if _within(x.expense_date, start, end)], today)
        revenue = summarize_student_finance([], payments, today)
        expense_months = defaultdict(Decimal)
        for x in expenses["active"]:
            expense_months[x.expense_date.strftime("%Y-%m")] += x.amount
        months = sorted(set(revenue["monthly_revenue"]) | set(expense_months))
        columns = ["Month", f"Revenue ({currency})", f"Active expense ({currency})", f"Net ({currency})"]
        for month in months:
            collected, spent = revenue["monthly_revenue"].get(month, ZERO), expense_months[month]
            rows.append(financial_row([month], [collected, spent, collected - spent]))
        kpis = [money_kpi("Revenue", revenue["collected"], "green"), money_kpi("Active expenses", expenses["active_total"], "red"),
                money_kpi("Net position", revenue["collected"] - expenses["active_total"])]
        summary += " Net position is gross completed student collections less active expenses, using payment_date and expense_date respectively."
    return _base_result(get_report_definition(slug), filters, columns, rows, kpis, summary)


REPORT_BUILDERS = {
    "expense-report": get_expense_report,
    "scholarship-report": get_scholarship_report,
    "discount-report": get_discount_report,
    "refund-report": get_refund_report,
    "supplier-balance": get_supplier_balance_report,
    "financial-assistance": get_financial_assistance_report,
}


def build_report(slug, params, currency):
    definition = get_report_definition(slug)
    if not definition:
        return None
    if slug in STUDENT_REPORTS:
        return get_student_report(slug, params, currency)
    builder = REPORT_BUILDERS.get(slug)
    if builder:
        return builder(params, currency)
    return _base_result(definition, [], [], [], [], f"This report is waiting for the actual {definition['dependency']}. No substitute records or financial values are shown.", export_enabled=False, note=definition["dependency"])

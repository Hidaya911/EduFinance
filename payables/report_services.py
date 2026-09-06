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
from .overdue_views import get_student_invoice_overdue_rows


ZERO = Decimal("0.00")


REPORT_DEFINITIONS = (
    {"id": "REP-001", "slug": "fee-collection", "title": "Fee Collection Report", "category": "Revenue & Collections", "status": "integration_pending", "description": "Expected, collected, remaining, and collection performance from student invoices and payments.", "dependency": "Student Invoice and Student Payment models"},
    {"id": "REP-002", "slug": "student-balance", "title": "Student Balance Report", "category": "Student Receivables", "status": "integration_pending", "description": "Student-level invoiced, paid, outstanding, and overdue balances.", "dependency": "Student Invoice, Student Payment, and academic placement data"},
    {"id": "REP-003", "slug": "payment-report", "title": "Payment Report", "category": "Revenue & Collections", "status": "integration_pending", "description": "Traceable student payment register with method, date, and receipt context.", "dependency": "Student Payment model"},
    {"id": "REP-004", "slug": "daily-collection", "title": "Daily Collection Report", "category": "Revenue & Collections", "status": "integration_pending", "description": "Daily student collections and transaction volume.", "dependency": "Student Payment model"},
    {"id": "REP-005", "slug": "monthly-revenue", "title": "Monthly Revenue Report", "category": "Revenue & Collections", "status": "integration_pending", "description": "Monthly recognized student revenue and collection trends.", "dependency": "Student Payment or recognized revenue model"},
    {"id": "REP-006", "slug": "expense-report", "title": "Expense Report", "category": "Operations & Payables", "status": "ready", "description": "Active and voided operating expenses with approval and payment context.", "dependency": ""},
    {"id": "REP-007", "slug": "revenue-vs-expense", "title": "Revenue vs Expense Report", "category": "Executive Analysis", "status": "partial", "description": "Verified expense trend with revenue held pending student-payment integration.", "dependency": "Student Payment or recognized revenue model"},
    {"id": "REP-008", "slug": "scholarship-report", "title": "Scholarship Report", "category": "Financial Adjustments", "status": "ready", "description": "Scholarship portfolio by lifecycle, academic year, and value type.", "dependency": ""},
    {"id": "REP-009", "slug": "discount-report", "title": "Discount Report", "category": "Financial Adjustments", "status": "ready", "description": "Discount register with fixed and percentage values reported separately.", "dependency": ""},
    {"id": "REP-010", "slug": "installment-report", "title": "Installment Report", "category": "Student Receivables", "status": "integration_pending", "description": "Installment schedules, due dates, payments, and remaining balances.", "dependency": "Installment or InstallmentPlan model"},
    {"id": "REP-011", "slug": "overdue-report", "title": "Overdue Payment Report", "category": "Student Receivables", "status": "integration_pending", "description": "Student receivables overdue under the official aging rules.", "dependency": "Student Invoice adapter for the existing Overdue service"},
    {"id": "REP-012", "slug": "refund-report", "title": "Refund Report", "category": "Financial Adjustments", "status": "partial", "description": "Real refund requests and workflow values without claiming payment-ledger reversal.", "dependency": "Student Payment model for validated payment linkage"},
    {"id": "REP-013", "slug": "supplier-balance", "title": "Supplier Balance Report", "category": "Operations & Payables", "status": "ready", "description": "Supplier billed, paid, and outstanding positions excluding cancelled and voided activity.", "dependency": ""},
    {"id": "REP-014", "slug": "payment-method", "title": "Payment Method Report", "category": "Revenue & Collections", "status": "integration_pending", "description": "Student collections grouped by payment method.", "dependency": "Student Payment model"},
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
    school = School.objects.first()
    return {
        "currency_code": school.default_currency if school and school.default_currency else "USD",
        "academic_year": school.current_academic_year.strip() if school and school.current_academic_year else "Not configured",
    }


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
    return _base_result(get_report_definition("refund-report"), filters, ["Refund", "Requested", "Student reference", "Payment reference", "Method", f"Amount ({currency})", "Workflow status", "Reason"], rows, kpis, "These are real refund workflow records. Payment references are currently text snapshots, so this report does not claim a verified student-ledger reversal.", note="Student Payment integration is still required to validate each refund against its originating collection.")


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


def get_revenue_vs_expense_report(params, currency):
    start, end = _date(params.get("date_from")), _date(params.get("date_to"))
    active = [x for x in Expense.objects.all() if x.record_status == Expense.RecordStatus.ACTIVE and _within(x.expense_date, start, end)]
    months = defaultdict(Decimal)
    for expense in active:
        months[expense.expense_date.strftime("%Y-%m")] += expense.amount or ZERO
    rows = [_row([datetime.strptime(month, "%Y-%m").strftime("%B %Y"), "Integration pending", _money(amount, currency), "Not calculated"], [month, "", _number(amount), ""], "partial") for month, amount in sorted(months.items(), reverse=True)]
    filters = [_filter("date_from", "Expense date from", params.get("date_from", ""), "date"), _filter("date_to", "Expense date to", params.get("date_to", ""), "date")]
    kpis = [{"label": "Verified expenses", "value": _money(sum((x.amount for x in active), ZERO), currency), "tone": "red"}, {"label": "Revenue", "value": "Integration pending", "tone": "amber"}, {"label": "Net position", "value": "Not calculated", "tone": "blue"}]
    return _base_result(get_report_definition("revenue-vs-expense"), filters, ["Month", f"Revenue ({currency})", f"Active expense ({currency})", f"Net ({currency})"], rows, kpis, "Only the expense side is available and it excludes voided expenses. Revenue and net position are never inferred or fabricated.", note="Student revenue integration is required before a complete comparison can be calculated.")


def get_overdue_integration_state():
    """Exercise the existing adapter without duplicating overdue rules."""
    return list(get_student_invoice_overdue_rows())


REPORT_BUILDERS = {
    "expense-report": get_expense_report,
    "scholarship-report": get_scholarship_report,
    "discount-report": get_discount_report,
    "refund-report": get_refund_report,
    "supplier-balance": get_supplier_balance_report,
    "financial-assistance": get_financial_assistance_report,
    "revenue-vs-expense": get_revenue_vs_expense_report,
}


def build_report(slug, params, currency):
    definition = get_report_definition(slug)
    if not definition:
        return None
    if slug == "overdue-report":
        get_overdue_integration_state()
    builder = REPORT_BUILDERS.get(slug)
    if builder:
        return builder(params, currency)
    return _base_result(definition, [], [], [], [], f"This report is waiting for the actual {definition['dependency']}. No substitute records or financial values are shown.", export_enabled=False, note=definition["dependency"])

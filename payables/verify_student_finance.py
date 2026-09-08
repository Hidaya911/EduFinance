"""Read-only live verification: run through manage.py shell (no test data writes).

python manage.py shell -c "exec(open('payables/verify_student_finance.py').read())"
"""

from decimal import Decimal
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from billing.models import Invoice, Payment, Installment
from myproject.views import dashboard_view
from payables.dashboard_services import get_dashboard_context
from payables.models import Expense
from payables.report_services import build_report, STUDENT_REPORTS
from school_config.models import School


today = timezone.localdate()
school = School.objects.first()
user = get_user_model().objects.filter(is_active=True).filter(
    Q(is_superuser=True) | Q(groups__name__in=("Super Admin", "Super Administrator"))
).first()
if user is None:
    raise RuntimeError("No existing active Super Admin is available for live rendering verification.")

context = get_dashboard_context(user)
data = context["student_finance"]
invoices = list(Invoice.objects.filter(school=school))
valid = [x for x in invoices if x.status in ("unpaid", "partially_paid", "paid", "overdue")]
payments = list(Payment.objects.filter(school=school))
completed = [x for x in payments if x.status == "completed"]
zero = Decimal("0.00")
expected = sum((x.total_amount for x in valid), zero)
collected = sum((x.amount for x in completed), zero)
remaining = sum((max(x.balance, zero) for x in valid), zero)
overdue = [x for x in valid if x.due_date < today and x.balance > zero]
overdue_total = sum((x.balance for x in overdue), zero)
revenue = sum((x.amount for x in completed if (x.payment_date.year, x.payment_date.month) == (today.year, today.month)), zero)
expense_records = list(Expense.objects.all())
expenses = sum((x.amount for x in expense_records if x.record_status == "active" and
                (x.expense_date.year, x.expense_date.month) == (today.year, today.month)), zero)
assert (data["expected"], data["collected"], data["outstanding"], data["month_revenue"]) == (expected, collected, remaining, revenue)
assert data["overdue_summary"]["total_overdue_amount"] == overdue_total
assert data["overdue_summary"]["overdue_invoice_count"] == len(overdue)
assert context["primary_kpis"][-1]["value"] == f"{revenue - expenses:,.2f}"
assert len(context["monthly_expenses"]) == 6
for point in context["monthly_expenses"]:
    month_number = datetime.strptime(point["label"], "%b").month
    month_key = (int(point["year"]), month_number)
    assert point["revenue"] == sum((x.amount for x in completed if (x.payment_date.year, x.payment_date.month) == month_key), zero)
    assert point["amount"] == sum((x.amount for x in expense_records if x.record_status == "active" and (x.expense_date.year, x.expense_date.month) == month_key), zero)
upcoming = [x for x in Installment.objects.filter(plan__school=school).select_related("plan__invoice")
            if x.plan.status == "active" and x.plan.invoice.status in ("unpaid", "partially_paid", "paid", "overdue")
            and x.plan.invoice.balance > zero and x.status != "paid" and x.due_date >= today and x.amount > x.paid_amount]
assert len(context["upcoming_installments"]) == min(5, len(upcoming))
assert len(context["recent_student_payments"]) == min(5, len(completed))
print({
    "currency": context["currency_code"], "academic_year": context["academic_year"],
    "invoices": len(invoices), "valid_invoices": len(valid), "valid_invoice_total": str(expected),
    "payments": len(payments), "valid_payments": len(completed), "valid_payment_total": str(collected),
    "outstanding": str(remaining), "overdue": str(overdue_total),
    "month_revenue": str(revenue), "month_expenses": str(expenses), "net_position": str(revenue - expenses),
    "overdue_invoice_count": len(overdue), "recent_payment_count": len(context["recent_student_payments"]),
    "upcoming_installment_count": len(context["upcoming_installments"]), "all_upcoming_installments": len(upcoming),
})
for slug in sorted(STUDENT_REPORTS):
    report = build_report(slug, {}, context["currency_code"])
    assert report["report"]["status"] == "ready" and report["export_enabled"]
    assert all(len(row["cells"]) == len(report["columns"]) == len(row["export"]) for row in report["rows"])
    print("Report", slug, "rows", len(report["rows"]))
for name in ("dashboard", "payables:reports_hub", "payables:overdue_list", "payables:payment_reminder_list"):
    print("URL", name, reverse(name))
request = RequestFactory().get(reverse("dashboard"))
request.user = user  # Existing authenticated principal; no login/session/audit writes.
response = dashboard_view(request)
assert response.status_code == 200
html = response.content.decode()
assert "Integration pending" not in html
for title in ("Collection Health", "Revenue vs Expense", "Important Notifications", "Receivable Risk",
              "Financial Adjustments", "Approval Queue", "Recent Expenses", "Recent Payment Activity",
              "Upcoming Installments", "Payment Reminder Health", "Supplier Snapshot", "Operational Shortcuts"):
    assert title in html, title
print("PASS: authenticated existing Super Admin dashboard rendered; source totals and reports verified.")

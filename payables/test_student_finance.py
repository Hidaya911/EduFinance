"""Isolated arithmetic/rendering tests; no records are written to Atlas."""

from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack

from bson import ObjectId
from django.test import SimpleTestCase
from django.template.loader import render_to_string

from accounts.core.models import AcademicYear
from billing.models import Invoice, Payment, Receipt, InstallmentPlan, Installment
from students.models import Student, Enrollment
from . import student_finance_services as finance
from .dashboard_services import _month_keys, get_dashboard_context
from .report_services import build_report, STUDENT_REPORTS


class StudentFinanceTests(SimpleTestCase):
    def setUp(self):
        self.today = date(2026, 1, 8)
        self.student = Student(pk=ObjectId(), student_number="TEST-ONLY", first_name="Test", last_name="Student")
        self.year = AcademicYear(pk=ObjectId(), name="Test year")
        self.enrollment = Enrollment(pk=ObjectId(), student_id=str(self.student.pk))

    def invoice(self, balance="60", days=1):
        return Invoice(pk=ObjectId(), invoice_number="TEST-INVOICE", student=self.student,
                       enrollment=self.enrollment, academic_year=self.year,
                       total_amount=Decimal("100"), paid_amount=Decimal("40"), balance=Decimal(balance),
                       due_date=self.today - timedelta(days=days), status="partially_paid",
                       created_at=datetime(2026, 1, 1, tzinfo=dt_timezone.utc))

    def payment(self, amount="40", day=None):
        return Payment(pk=ObjectId(), payment_number="TEST-PAYMENT", student=self.student,
                       payment_date=day or self.today, amount=Decimal(amount), status="completed", payment_method="cash")

    def snapshot(self, invoices=(), payments=(), installments=()):
        overdue = finance.invoice_overdue_rows(invoices, self.today)
        return {**finance.summarize_student_finance(invoices, payments, self.today),
                "invoices": list(invoices), "payments": list(payments), "installments": list(installments),
                "overdue_rows": overdue, "overdue_summary": finance.summarize_overdue_rows(overdue)}

    def test_canonical_balance_and_calendar_month(self):
        result = finance.summarize_student_finance(
            [self.invoice(), self.invoice(balance="-1")],
            [self.payment(), self.payment("7", date(2025, 12, 31))], self.today)
        self.assertEqual(result["expected"], Decimal("200"))
        self.assertEqual(result["collected"], Decimal("47"))
        self.assertEqual(result["outstanding"], Decimal("60"))
        self.assertEqual(result["month_revenue"], Decimal("40"))
        self.assertEqual(result["collection_percent"], Decimal("23.5"))

    def test_zero_and_overcollection_are_not_misleading(self):
        empty = finance.summarize_student_finance([], [], self.today)
        self.assertEqual(empty["expected"], Decimal("0"))
        self.assertIsNone(empty["collection_percent"])
        result = finance.summarize_student_finance([self.invoice()], [self.payment("120")], self.today)
        self.assertEqual(result["collection_percent"], Decimal("120"))

    def test_valid_status_queries(self):
        with patch.object(Invoice.objects, "filter") as invoices, patch.object(Payment.objects, "filter") as payments:
            finance.valid_invoices("school")
            finance.valid_payments("school")
        self.assertEqual(set(invoices.call_args.kwargs["status__in"]), {"unpaid", "partially_paid", "paid", "overdue"})
        payments.assert_called_once_with(school="school", status="completed")

    def test_aging_boundaries_and_due_today(self):
        cases = [(1, "1_7"), (7, "1_7"), (8, "8_30"), (30, "8_30"), (31, "31_60"), (60, "31_60"), (61, "60_plus")]
        for days, bucket in cases:
            with self.subTest(days=days):
                row = finance.invoice_overdue_rows([self.invoice(days=days)], self.today)[0]
                self.assertEqual(row["aging_bucket"], bucket)
                self.assertEqual(row["outstanding_amount"], Decimal("60"))
        for item in (self.invoice(days=0), self.invoice(days=-1), self.invoice(balance="0"), self.invoice(balance="-1")):
            self.assertEqual(finance.invoice_overdue_rows([item], self.today), [])

    def test_installment_remaining_and_read_only_status(self):
        item = Installment(amount=Decimal("50"), paid_amount=Decimal("20"), due_date=self.today - timedelta(days=2))
        self.assertEqual(finance.installment_remaining(item), Decimal("30"))
        self.assertEqual(finance.installment_status(item, self.today), "partially_paid")
        item.paid_amount = Decimal("0")
        self.assertEqual(finance.installment_status(item, self.today), "overdue")
        item.paid_amount = Decimal("60")
        self.assertEqual(finance.installment_remaining(item), Decimal("0"))
        self.assertEqual(finance.installment_status(item, self.today), "paid")

    def test_receipt_absent_issued_and_void(self):
        payment = self.payment()
        payment._state.fields_cache["receipt"] = None
        self.assertEqual(finance.issued_receipt(payment), "")
        receipt = Receipt(payment=payment, receipt_number="TEST-RECEIPT", status="issued")
        self.assertEqual(finance.issued_receipt(payment), "TEST-RECEIPT")
        receipt.status = "void"
        self.assertEqual(finance.issued_receipt(payment), "")

    def test_six_months_cross_year(self):
        self.assertEqual(_month_keys(self.today), ["2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01"])

    def test_reminder_reference_requires_exact_number_and_student(self):
        invoice = self.invoice()
        invoices = {invoice.invoice_number: invoice}
        reminder = SimpleNamespace(invoice_reference=" TEST-INVOICE ", student_id=self.student.pk)
        self.assertIs(finance.reminder_invoice(reminder, invoices), invoice)
        reminder.student_id = ObjectId()
        self.assertIsNone(finance.reminder_invoice(reminder, invoices))
        reminder.student_id = self.student.pk
        reminder.invoice_reference = "TEST"
        self.assertIsNone(finance.reminder_invoice(reminder, invoices))

    def test_current_academic_year_precedes_legacy_text(self):
        school = SimpleNamespace(default_currency="LBP", current_academic_year="Legacy")
        with patch.object(AcademicYear.objects, "filter") as query:
            query.return_value.order_by.return_value.first.return_value = self.year
            self.assertEqual(finance.school_context(school), {"currency_code": "LBP", "academic_year": "Test year"})
            query.return_value.order_by.return_value.first.return_value = None
            self.assertEqual(finance.school_context(school)["academic_year"], "Legacy")

    def test_all_reports_empty_sources_are_ready_with_zero_values(self):
        with patch("payables.report_services.get_student_finance_data", return_value=self.snapshot()), patch("payables.report_services.Expense.objects.all", return_value=[]):
            for slug in STUDENT_REPORTS:
                with self.subTest(slug=slug):
                    result = build_report(slug, {}, "LBP")
                    self.assertEqual(result["report"]["status"], "ready")
                    self.assertTrue(result["export_enabled"])
                    self.assertEqual(result["rows"], [])
                    self.assertNotIn("Integration pending", str(result))

    def test_reports_match_source_totals_and_filters(self):
        payment = self.payment()
        payment._state.fields_cache["receipt"] = None
        data = self.snapshot([self.invoice()], [payment])
        with patch("payables.report_services.get_student_finance_data", return_value=data), patch("payables.report_services.timezone.localdate", return_value=self.today):
            report = build_report("fee-collection", {}, "LBP")
            self.assertEqual([x["value"] for x in report["kpis"]], ["LBP 100.00", "LBP 40.00", "LBP 60.00", "40.00%"])
            report = build_report("payment-report", {"date_to": "2026-01-07"}, "LBP")
            self.assertEqual(report["rows"], [])
            self.assertEqual(report["kpis"][0]["value"], "LBP 0.00")
            overdue = build_report("overdue-report", {"aging": "1_7"}, "LBP")
            self.assertEqual(overdue["rows"][0]["export"][-1], "60.00")

    def test_revenue_expense_includes_months_with_only_one_source(self):
        payment = self.payment()
        payment._state.fields_cache["receipt"] = None
        expense = SimpleNamespace(amount=Decimal("75"), expense_date=date(2025, 12, 31), record_status="active", approval_status="approved")
        with patch("payables.report_services.get_student_finance_data", return_value=self.snapshot([], [payment])), patch("payables.report_services.Expense.objects.all", return_value=[expense]):
            report = build_report("revenue-vs-expense", {}, "LBP")
            self.assertEqual([x["export"] for x in report["rows"]], [["2025-12", "0.00", "75.00", "-75.00"], ["2026-01", "40.00", "0.00", "40.00"]])

    def test_empty_dashboard_renders_zero_and_preserves_sections(self):
        data = {**self.snapshot(), "recent_payments": [], "upcoming_installments": []}
        user = SimpleNamespace(is_authenticated=True, get_full_name=lambda: "Test", get_username=lambda: "test", has_perm=lambda permission: False)
        with ExitStack() as stack:
            for name in ("Expense", "ExpenseCategory", "SupplierBill", "SupplierPayment", "Supplier", "Scholarship", "Discount", "Refund", "FinancialAssistanceRequest", "ApprovalRequest", "PaymentReminder"):
                stack.enter_context(patch(f"payables.dashboard_services.{name}.objects.all", return_value=[]))
            stack.enter_context(patch("payables.dashboard_services.School.objects.first", return_value=None))
            stack.enter_context(patch("payables.dashboard_services.school_context", return_value={"currency_code": "LBP", "academic_year": "Test year"}))
            stack.enter_context(patch("payables.dashboard_services.get_student_finance_data", return_value=data))
            stack.enter_context(patch("payables.dashboard_services.get_user_notification_preview", return_value=[]))
            context = get_dashboard_context(user)
        self.assertTrue(all(x["available"] and x["value"] == "0.00" for x in context["primary_kpis"]))
        html = render_to_string("dashboard.html", context)
        self.assertNotIn("Integration pending", html)
        self.assertIn("No completed student payments", html)
        self.assertIn("No upcoming unpaid installments", html)
        self.assertIn("LBP 0.00", html)
        self.assertEqual(len(context["monthly_expenses"]), 6)

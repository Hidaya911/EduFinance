"""Read-only receipt presentation checks; no financial records are created."""
from datetime import datetime, date, timezone
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory
from django.urls import reverse

from billing.services.receipt_service import receipt_document_context
from billing.views.receipt_views import receipt_print, receipt_detail


class ReceiptPresentationTests(SimpleTestCase):
    def setUp(self):
        self.payment = NS(pk="payment", amount=Decimal("125.50"), status="completed", payment_number="TEST-PAYMENT",
                          payment_date=date(2026, 9, 8), get_status_display=lambda: "Completed",
                          get_payment_method_display=lambda: "Cash", allocations=Mock(),
                          received_by=NS(get_full_name=lambda: "Test Cashier", get_username=lambda: "cashier"))
        self.payment.allocations.all.return_value = []
        self.receipt = NS(pk="receipt", receipt_number="TEST-RECEIPT", payment=self.payment, amount=Decimal("125.50"),
                          status="issued", issued_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
                          get_status_display=lambda: "Issued", student=NS(full_name="Test Student", student_number="TEST-STUDENT"),
                          school=NS(name="Test School", logo=None, default_currency="LBP", address="", phone="", email="", website=""))

    def test_real_amount_currency_cashier_and_no_allocations(self):
        context = receipt_document_context(self.receipt)
        self.assertTrue(context["valid_receipt"])
        self.assertEqual(context["currency_code"], "LBP")
        self.assertEqual(context["cashier"], "Test Cashier")
        html = render_to_string("billing/receipts/document.html", context)
        self.assertIn("125.50", html)
        self.assertIn("LBP", html)
        self.assertNotIn("USD", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("Guardian", html)
        self.assertEqual(self.receipt.amount, Decimal("125.50"))

    def test_void_receipt_or_payment_never_looks_valid(self):
        for which in ("receipt", "payment"):
            self.receipt.status = "void" if which == "receipt" else "issued"
            self.payment.status = "void" if which == "payment" else "completed"
            context = receipt_document_context(self.receipt)
            self.assertFalse(context["valid_receipt"])
            html = render_to_string("billing/receipts/document.html", context)
            self.assertIn("NOT VALID AS PROOF OF PAYMENT", html)
            self.assertNotIn("Thank you for your payment", html)

    def test_allocation_amount_is_not_invoice_total(self):
        invoice = NS(invoice_number="TEST-INVOICE", academic_year=NS(name="2025-2026"),
                     enrollment=NS(grade_id="g", classroom_id="c"), fee_structure_id=None, status="partially_paid")
        self.payment.allocations.all.return_value = [NS(invoice=invoice, amount=Decimal("125.50"))]
        with patch("billing.services.receipt_service.Grade.objects.all", return_value=[NS(pk="g", name="Grade 2")]), patch("billing.services.receipt_service.SchoolClass.objects.all", return_value=[NS(pk="c", name="A")]):
            context = receipt_document_context(self.receipt)
        self.assertEqual(context["academic_years"], "2025-2026")
        self.assertEqual(context["placements"], "Grade 2 / A")
        self.assertEqual(context["allocation_rows"][0]["amount"], Decimal("125.50"))
        self.assertFalse(context["allocation_mismatch"])

    def test_discrepancy_is_visible_without_changing_amount(self):
        self.payment.amount = Decimal("100")
        context = receipt_document_context(self.receipt)
        self.assertTrue(context["payment_mismatch"])
        self.assertIn("Record discrepancy", render_to_string("billing/receipts/document.html", context))
        self.assertEqual(self.receipt.amount, Decimal("125.50"))

    def test_print_is_standalone_and_has_no_app_chrome(self):
        html = render_to_string("billing/receipts/print.html", receipt_document_context(self.receipt))
        self.assertIn("PAYMENT RECEIPT", html)
        self.assertNotIn("top-navbar", html)
        self.assertNotIn('class="sidebar"', html)
        self.assertIn("Print / Save as PDF", html)
        self.assertNotIn("data-receipt-auto-print", html)

    def test_detail_and_print_keep_authorization(self):
        request = RequestFactory().get("/")
        request.user = NS(is_authenticated=True, is_superuser=False, groups=Mock())
        request.user.groups.values_list.return_value = []
        for view in (receipt_detail, receipt_print):
            with self.assertRaises(PermissionDenied):
                view(request, "receipt")
        request.user = NS(is_authenticated=False)
        for view in (receipt_detail, receipt_print):
            self.assertEqual(view(request, "receipt").status_code, 302)

    def test_print_keeps_school_scoping_and_missing_receipt_404(self):
        request = RequestFactory().get(reverse("billing:receipt_print", args=["missing"]))
        request.user = NS(is_authenticated=True, is_superuser=True)
        with patch("billing.views.receipt_views.get_current_school", return_value="configured-school"), patch("billing.views.receipt_views.receipt_queryset") as query, patch("billing.views.receipt_views.get_object_or_404", side_effect=Http404):
            with self.assertRaises(Http404):
                receipt_print(request, "missing")
            query.assert_called_once_with("configured-school")

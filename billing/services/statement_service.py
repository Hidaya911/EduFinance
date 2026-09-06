from decimal import Decimal
from django.db.models import Sum
from billing.models import Invoice, Payment, Receipt, InstallmentPlan

def build_student_statement(student,start_date=None,end_date=None):
    invoices=Invoice.objects.filter(student=student).exclude(status=Invoice.STATUS_VOID)
    payments=Payment.objects.filter(student=student,status="completed")
    receipts=Receipt.objects.filter(student=student,status="issued")
    plans=InstallmentPlan.objects.filter(student=student).exclude(status="cancelled")
    if start_date:
        invoices=invoices.filter(created_at__date__gte=start_date); payments=payments.filter(payment_date__gte=start_date); receipts=receipts.filter(issued_at__date__gte=start_date)
    if end_date:
        invoices=invoices.filter(created_at__date__lte=end_date); payments=payments.filter(payment_date__lte=end_date); receipts=receipts.filter(issued_at__date__lte=end_date)
    totals=invoices.aggregate(invoiced=Sum("total_amount"),outstanding=Sum("balance")); paid=payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return {"student":student,"invoices":invoices.order_by("-created_at"),"payments":payments.order_by("-payment_date"),"receipts":receipts.order_by("-issued_at"),"plans":plans.order_by("-created_at"),"total_invoiced":totals["invoiced"] or Decimal("0.00"),"total_paid":paid,"total_outstanding":totals["outstanding"] or Decimal("0.00")}

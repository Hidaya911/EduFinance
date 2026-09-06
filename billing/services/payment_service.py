from decimal import Decimal
from billing.models import Payment, PaymentAllocation, Receipt, Installment
from .common import generate_document_number

def _apply_payment_to_installments(invoice,amount):
    remaining=amount
    for inst in Installment.objects.filter(plan__invoice=invoice,plan__status="active").order_by("due_date","installment_number"):
        if remaining<=0: break
        open_amount=inst.amount-inst.paid_amount
        if open_amount<=0: continue
        applied=min(open_amount,remaining)
        inst.paid_amount+=applied; inst.save(update_fields=["paid_amount"]); inst.refresh_status(); remaining-=applied
    for plan in invoice.installment_plans.filter(status="active"):
        if not plan.installments.exclude(status="paid").exists():
            plan.status="completed"; plan.save(update_fields=["status"])

def record_payment(*,school,student,payment_date,payment_method,allocations,received_by,notes=""):
    cleaned=[]; total=Decimal("0.00")
    for invoice,amount in allocations:
        amount=Decimal(amount)
        if amount<=0: raise ValueError("Allocation amounts must be greater than zero.")
        if invoice.student_id!=student.pk: raise ValueError("Every invoice must belong to the selected student.")
        if invoice.status==invoice.STATUS_VOID: raise ValueError("Cannot pay a void invoice.")
        if amount>invoice.balance: raise ValueError(f"Allocation for {invoice.invoice_number} exceeds its outstanding balance.")
        cleaned.append((invoice,amount)); total+=amount
    if total<=0: raise ValueError("Payment amount must be greater than zero.")
    payment=Payment(school=school,payment_number=generate_document_number("PAY"),student=student,payment_date=payment_date,amount=total,payment_method=payment_method,status="completed",received_by=received_by,notes=notes)
    payment.full_clean(); payment.save()
    for invoice,amount in cleaned:
        PaymentAllocation.objects.create(payment=payment,invoice=invoice,amount=amount)
        invoice.paid_amount+=amount; invoice.refresh_financial_status(); _apply_payment_to_installments(invoice,amount)
    Receipt.objects.create(school=school,receipt_number=generate_document_number(school.receipt_prefix or "REC"),payment=payment,student=student,amount=total,status="issued")
    return payment

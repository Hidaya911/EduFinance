from decimal import Decimal
from billing.models import Invoice, InvoiceItem
from .common import generate_document_number

def create_invoice_from_fee_structure(*,school,student,enrollment,academic_year,fee_structure,due_date,created_by):
    if str(enrollment.student_id)!=str(student.pk): raise ValueError("The selected enrollment does not belong to the selected student.")
    if fee_structure.academic_year_id!=academic_year.pk: raise ValueError("Fee structure academic year does not match the selected academic year.")
    invoice=Invoice(school=school,invoice_number=generate_document_number(school.invoice_prefix or "INV"),student=student,enrollment=enrollment,academic_year=academic_year,fee_structure=fee_structure,total_amount=fee_structure.total_amount,paid_amount=Decimal("0.00"),balance=fee_structure.total_amount,status=Invoice.STATUS_UNPAID,due_date=due_date,created_by=created_by)
    invoice.full_clean(); invoice.save()
    for source in fee_structure.items.all():
        InvoiceItem.objects.create(invoice=invoice,fee_category=source.fee_category,category_name=source.fee_category.name,description=source.fee_category.description or "",amount=source.amount)
    invoice.refresh_financial_status(); return invoice

"""Read-only presentation of existing receipts and payment allocations."""
from decimal import Decimal
import base64
import mimetypes
from django.db.models import Prefetch
from billing.models import Receipt, PaymentAllocation
from school_config.models import Grade, SchoolClass


def receipt_queryset(school):
    return Receipt.objects.filter(school=school).select_related(
        "school", "student", "payment__received_by",
    ).prefetch_related(Prefetch(
        "payment__allocations",
        queryset=PaymentAllocation.objects.select_related(
            "invoice__academic_year", "invoice__enrollment", "invoice__fee_structure",
        ).order_by("invoice__invoice_number", "pk"),
    ))


def receipt_is_valid(receipt):
    return receipt.status == "issued" and receipt.payment.status == "completed"


def receipt_document_context(receipt):
    """Use receipt.amount as the issued amount; never reconstruct or write it."""
    allocations = list(receipt.payment.allocations.all())
    grades = {str(x.pk): x.name for x in Grade.objects.all()} if allocations else {}
    classes = {str(x.pk): x.name for x in SchoolClass.objects.all()} if allocations else {}
    rows, placements = [], set()
    for allocation in allocations:
        invoice = allocation.invoice
        placement = " / ".join(filter(None, (
            grades.get(str(invoice.enrollment.grade_id)),
            classes.get(str(invoice.enrollment.classroom_id)),
        )))
        if placement:
            placements.add(placement)
        rows.append({"invoice": invoice,
                     "description": invoice.fee_structure.name if invoice.fee_structure_id else "Invoice payment",
                     "amount": allocation.amount})
    allocated_total = sum((x.amount for x in allocations), Decimal("0.00"))
    cashier = receipt.payment.received_by
    logo_url = ""
    if receipt.school.logo:
        try:
            content_type = mimetypes.guess_type(receipt.school.logo.name)[0]
            if content_type in {"image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"}:
                with receipt.school.logo.open("rb") as logo:
                    data = logo.read(2 * 1024 * 1024 + 1)
                if len(data) <= 2 * 1024 * 1024:
                    logo_url = f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"
        except (OSError, ValueError, NotImplementedError):
            pass
    return {
        "receipt": receipt, "school": receipt.school, "payment": receipt.payment,
        "currency_code": receipt.school.default_currency,
        "logo_url": logo_url, "allocation_rows": rows,
        "academic_years": ", ".join(sorted({x.invoice.academic_year.name for x in allocations})),
        "placements": ", ".join(sorted(placements)),
        "cashier": cashier.get_full_name().strip() or cashier.get_username(),
        "valid_receipt": receipt_is_valid(receipt),
        "allocation_mismatch": bool(allocations) and allocated_total != receipt.amount,
        "payment_mismatch": receipt.amount != receipt.payment.amount,
    }

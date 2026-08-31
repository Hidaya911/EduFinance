from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    SupplierBill,
    SupplierPayment,
    Expense,
    EmployeeFinancialTransaction,
)

# ============================================================
# CREATE / POST SUPPLIER PAYMENT
# ============================================================

def create_supplier_payment(
    *,
    bill,
    payment_date,
    amount,
    payment_method,
    reference="",
    notes="",
):

    amount = Decimal(
        str(amount)
    )

    # Refetch the bill so we use the latest
    # balance before applying a payment.
    bill = SupplierBill.objects.get(
        pk=bill.pk
    )

    if (
        bill.status
        == SupplierBill.Status.CANCELLED
    ):

        raise ValidationError(
            "Payments cannot be recorded against a cancelled bill."
        )

    if (
        bill.remaining_amount
        <= Decimal("0.00")
    ):

        raise ValidationError(
            "This supplier bill is already fully paid."
        )

    if amount <= 0:

        raise ValidationError(
            "Payment amount must be greater than zero."
        )

    if amount > bill.remaining_amount:

        raise ValidationError(
            (
                "Payment amount cannot be greater "
                "than the bill's remaining balance."
            )
        )

    payment = SupplierPayment(
        bill=bill,
        supplier=bill.supplier,
        payment_date=payment_date,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        notes=notes,
        status=SupplierPayment.Status.POSTED,
    )

    payment.full_clean()

    # --------------------------------------------------------
    # Save payment first.
    # If updating the bill fails, remove this newly-created
    # record as an internal rollback.
    # --------------------------------------------------------

    payment.save()

    previous_amount_paid = (
        bill.amount_paid
        or Decimal("0.00")
    )

    try:

        bill.amount_paid = (
            previous_amount_paid
            + amount
        )

        # SupplierBill.save() recalculates:
        # remaining_amount
        # status
        bill.save()

    except Exception:

        # Internal rollback only.
        # Normal users never delete financial payments.
        payment.delete()

        raise

    return payment


# ============================================================
# VOID SUPPLIER PAYMENT
# ============================================================

def void_supplier_payment(
    *,
    payment,
    reason="",
):

    payment = SupplierPayment.objects.get(
        pk=payment.pk
    )

    if (
        payment.status
        == SupplierPayment.Status.VOIDED
    ):

        raise ValidationError(
            "This supplier payment is already voided."
        )

    bill = SupplierBill.objects.get(
        pk=payment.bill_id
    )

    previous_amount_paid = (
        bill.amount_paid
        or Decimal("0.00")
    )

    corrected_amount_paid = (
        previous_amount_paid
        - payment.amount
    )

    if corrected_amount_paid < 0:

        corrected_amount_paid = (
            Decimal("0.00")
        )

    # --------------------------------------------------------
    # Reverse bill impact first.
    # --------------------------------------------------------

    bill.amount_paid = (
        corrected_amount_paid
    )

    bill.save()

    try:

        payment.status = (
            SupplierPayment.Status.VOIDED
        )

        payment.void_reason = (
            reason.strip()
            if reason
            else ""
        )

        payment.voided_at = (
            timezone.now()
        )

        payment.save()

    except Exception:

        # Restore the bill if changing the
        # payment record unexpectedly fails.

        bill.amount_paid = (
            previous_amount_paid
        )

        bill.save()

        raise

    return payment



# ============================================================
# VOID EXPENSE
# ============================================================

def void_expense(
    *,
    expense,
    user,
    reason="",
):

    expense = Expense.objects.get(
        pk=expense.pk
    )

    if (
        expense.record_status
        == Expense.RecordStatus.VOIDED
    ):

        raise ValidationError(
            "This expense is already voided."
        )

    expense.record_status = (
        Expense.RecordStatus.VOIDED
    )

    expense.void_reason = (
        reason.strip()
        if reason
        else ""
    )

    expense.voided_at = (
        timezone.now()
    )

    expense.voided_by = (
        user
    )

    expense.save()

    return expense




# ============================================================
# VOID EMPLOYEE FINANCIAL TRANSACTION
# ============================================================

def void_employee_financial_transaction(
    *,
    transaction,
    user,
    reason="",
):

    transaction = (
        EmployeeFinancialTransaction
        .objects
        .get(
            pk=transaction.pk
        )
    )

    if (
        transaction.status
        ==
        EmployeeFinancialTransaction
        .Status
        .VOIDED
    ):

        raise ValidationError(
            (
                "This employee financial "
                "transaction is already voided."
            )
        )

    transaction.status = (
        EmployeeFinancialTransaction
        .Status
        .VOIDED
    )

    transaction.void_reason = (
        reason.strip()
        if reason
        else ""
    )

    transaction.voided_at = (
        timezone.now()
    )

    transaction.voided_by = (
        user
    )

    transaction.save()

    return transaction
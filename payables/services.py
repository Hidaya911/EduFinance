from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    ApprovalRequest,
    Discount,
    Scholarship,
)

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



def submit_approval_request(
    approval_request,
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    if (
        approval_request.status
        !=
        ApprovalRequest.Status.REQUESTED
    ):

        raise ValidationError(
            (
                "Only requested approval records "
                "can be submitted."
            )
        )

    approval_request.status = (
        ApprovalRequest.Status.PENDING
    )

    approval_request.submitted_at = (
        timezone.now()
    )

    approval_request.save(
        update_fields=[
            "status",
            "submitted_at",
            "updated_at",
        ]
    )

    return approval_request


def approve_approval_request(
    approval_request,
    approver,
    comments="",
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    if (
        approval_request.status
        !=
        ApprovalRequest.Status.PENDING
    ):

        raise ValidationError(
            (
                "Only pending approval requests "
                "can be approved."
            )
        )

    approval_request.status = (
        ApprovalRequest.Status.APPROVED
    )

    approval_request.approver = (
        approver
    )

    approval_request.decision_comments = (
        comments.strip()
    )

    approval_request.decided_at = (
        timezone.now()
    )

    approval_request.save(
        update_fields=[
            "status",
            "approver",
            "decision_comments",
            "decided_at",
            "updated_at",
        ]
    )

    return approval_request


def reject_approval_request(
    approval_request,
    approver,
    comments,
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    if (
        approval_request.status
        !=
        ApprovalRequest.Status.PENDING
    ):

        raise ValidationError(
            (
                "Only pending approval requests "
                "can be rejected."
            )
        )

    comments = (
        comments
        .strip()
    )

    if not comments:

        raise ValidationError(
            (
                "A rejection reason is required."
            )
        )

    approval_request.status = (
        ApprovalRequest.Status.REJECTED
    )

    approval_request.approver = (
        approver
    )

    approval_request.decision_comments = (
        comments
    )

    approval_request.decided_at = (
        timezone.now()
    )

    approval_request.save(
        update_fields=[
            "status",
            "approver",
            "decision_comments",
            "decided_at",
            "updated_at",
        ]
    )

    return approval_request


def process_approval_request(
    approval_request,
    user,
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    if (
        approval_request.status
        !=
        ApprovalRequest.Status.APPROVED
    ):

        raise ValidationError(
            (
                "Only approved requests "
                "can be marked as processed."
            )
        )

    # --------------------------------------------------------
    # DISCOUNT PROCESSING PROTECTION
    # --------------------------------------------------------

    if (
        approval_request.operation_type
        ==
        ApprovalRequest.OperationType.DISCOUNT
        and
        (
            approval_request.related_entity_type
            or ""
        ).strip().lower()
        ==
        "discount"
    ):

        discount = get_discount_for_approval(
            approval_request
        )

        if (
            discount.status
            !=
            Discount.Status.APPLIED
        ):

            raise ValidationError(
                (
                    "This discount cannot be marked as "
                    "processed until it has been applied "
                    "to its invoice."
                )
            )

    # --------------------------------------------------------
    # SCHOLARSHIP PROCESSING PROTECTION
    # --------------------------------------------------------

    if (
        approval_request.operation_type
        ==
        ApprovalRequest.OperationType.SCHOLARSHIP
        and
        (
            approval_request.related_entity_type
            or ""
        ).strip().lower()
        ==
        "scholarship"
    ):

        scholarship = get_scholarship_for_approval(
            approval_request
        )

        if (
            scholarship.status
            !=
            Scholarship.Status.APPLIED
        ):

            raise ValidationError(
                (
                    "This scholarship cannot be marked as "
                    "processed until it has been applied to "
                    "the student's financial account."
                )
            )

    approval_request.status = (
        ApprovalRequest.Status.PROCESSED
    )

    approval_request.processed_by = (
        user
    )

    approval_request.processed_at = (
        timezone.now()
    )

    approval_request.save(
        update_fields=[
            "status",
            "processed_by",
            "processed_at",
            "updated_at",
        ]
    )

    return approval_request


# ============================================================
# DISCOUNT — CREATE
# ============================================================

def create_discount(
    *,
    user,
    student_reference,
    invoice_reference,
    discount_type,
    value_type,
    value,
    reason,
    discount_date,
    requires_approval=False,
):

    discount = Discount(
        student_reference=student_reference,
        invoice_reference=invoice_reference,
        discount_type=discount_type,
        value_type=value_type,
        value=value,
        reason=reason,
        discount_date=discount_date,
        requires_approval=requires_approval,
        requested_by=user,
        status=Discount.Status.DRAFT,
    )

    discount.full_clean()

    discount.save()

    return discount


# ============================================================
# DISCOUNT — UPDATE DRAFT
# ============================================================

def update_discount(
    *,
    discount,
    student_reference,
    invoice_reference,
    discount_type,
    value_type,
    value,
    reason,
    discount_date,
    requires_approval,
):

    discount = (
        Discount.objects.get(
            pk=discount.pk
        )
    )

    if (
        discount.status
        != Discount.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only draft discounts "
                "can be edited."
            )
        )

    discount.student_reference = (
        student_reference
    )

    discount.invoice_reference = (
        invoice_reference
    )

    discount.discount_type = (
        discount_type
    )

    discount.value_type = (
        value_type
    )

    discount.value = (
        value
    )

    discount.reason = (
        reason
    )

    discount.discount_date = (
        discount_date
    )

    discount.requires_approval = (
        requires_approval
    )

    discount.full_clean()

    discount.save()

    return discount


# ============================================================
# DISCOUNT — APPROVAL DESCRIPTION
# ============================================================

def _discount_approval_description(
    discount,
):

    if (
        discount.value_type
        ==
        Discount.ValueType.PERCENTAGE
    ):

        value_description = (
            f"{discount.value:.2f}%"
        )

    else:

        value_description = (
            f"Fixed amount {discount.value:.2f}"
        )

    return (
        f"Discount {discount.discount_number} "
        f"for student "
        f"{discount.student_reference}. "
        f"Invoice: "
        f"{discount.invoice_reference}. "
        f"Type: "
        f"{discount.get_discount_type_display()}. "
        f"Value: "
        f"{value_description}."
    )


# ============================================================
# DISCOUNT — SUBMIT
# ============================================================

def submit_discount(
    *,
    discount,
):

    discount = (
        Discount.objects.get(
            pk=discount.pk
        )
    )

    if (
        discount.status
        != Discount.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only draft discounts "
                "can be submitted."
            )
        )

    # --------------------------------------------------------
    # NO APPROVAL REQUIRED
    # --------------------------------------------------------

    if not discount.requires_approval:

        discount.status = (
            Discount.Status.APPROVED
        )

        discount.approved_at = (
            timezone.now()
        )

        discount.full_clean()

        discount.save()

        return discount


    # --------------------------------------------------------
    # APPROVAL REQUIRED
    # --------------------------------------------------------

    if discount.approval_request_id:

        raise ValidationError(
            (
                "This discount already has "
                "an approval request."
            )
        )

    approval_amount = None

    if (
        discount.value_type
        ==
        Discount.ValueType.FIXED_AMOUNT
    ):

        approval_amount = (
            discount.value
        )

    approval_request = ApprovalRequest(
        operation_type=
            ApprovalRequest
            .OperationType
            .DISCOUNT,

        title=(
            f"Discount approval — "
            f"{discount.discount_number}"
        ),

        description=(
            _discount_approval_description(
                discount
            )
        ),

        amount=approval_amount,

        related_entity_type="Discount",

        related_entity_id=str(
            discount.pk
        ),

        requester=(
            discount.requested_by
        ),

        request_reason=(
            discount.reason
        ),

        status=
            ApprovalRequest
            .Status
            .REQUESTED,
    )

    approval_request.full_clean()

    approval_request.save()

    try:

        approval_request = (
            submit_approval_request(
                approval_request
            )
        )

        discount.approval_request = (
            approval_request
        )

        discount.status = (
            Discount.Status
            .PENDING_APPROVAL
        )

        discount.full_clean()

        discount.save()

    except Exception:

        # This approval request was only
        # created as part of this operation.
        # Delete it if linking the discount
        # fails so we do not leave an orphan.
        approval_request.delete()

        raise

    return discount


# ============================================================
# GET DISCOUNT LINKED TO APPROVAL
# ============================================================

def get_discount_for_approval(
    approval_request,
):

    if (
        approval_request.operation_type
        !=
        ApprovalRequest
        .OperationType
        .DISCOUNT
    ):

        raise ValidationError(
            (
                "This approval request "
                "is not for a discount."
            )
        )

    entity_type = (
        approval_request
        .related_entity_type
        or ""
    ).strip()

    entity_id = (
        approval_request
        .related_entity_id
        or ""
    ).strip()

    if (
        entity_type.lower()
        != "discount"
        or
        not entity_id
    ):

        raise ValidationError(
            (
                "This approval request is not "
                "linked to a valid discount."
            )
        )

    try:

        discount = (
            Discount.objects.get(
                pk=entity_id
            )
        )

    except Discount.DoesNotExist:

        raise ValidationError(
            (
                "The discount linked to this "
                "approval request no longer exists."
            )
        )

    if (
        not discount.approval_request_id
        or
        str(
            discount.approval_request_id
        )
        !=
        str(
            approval_request.pk
        )
    ):

        raise ValidationError(
            (
                "The approval request is not "
                "linked to this discount record."
            )
        )

    return discount


# ============================================================
# APPROVE DISCOUNT APPROVAL
# ============================================================

def approve_discount_approval(
    *,
    approval_request,
    approver,
    comments="",
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    discount = (
        get_discount_for_approval(
            approval_request
        )
    )

    if (
        discount.status
        !=
        Discount.Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "The linked discount is not "
                "pending approval."
            )
        )

    approval_request = (
        approve_approval_request(
            approval_request,
            approver,
            comments,
        )
    )

    try:

        discount.status = (
            Discount.Status.APPROVED
        )

        discount.approved_by = (
            approver
        )

        discount.approved_at = (
            approval_request.decided_at
            or timezone.now()
        )

        discount.full_clean()

        discount.save()

    except Exception:

        # Compensating rollback.
        approval_request.status = (
            ApprovalRequest.Status.PENDING
        )

        approval_request.approver = None

        approval_request.decision_comments = ""

        approval_request.decided_at = None

        approval_request.save()

        raise

    return discount


# ============================================================
# REJECT DISCOUNT APPROVAL
# ============================================================

def reject_discount_approval(
    *,
    approval_request,
    approver,
    comments,
):

    approval_request = (
        ApprovalRequest.objects.get(
            pk=approval_request.pk
        )
    )

    discount = (
        get_discount_for_approval(
            approval_request
        )
    )

    if (
        discount.status
        !=
        Discount.Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "The linked discount is not "
                "pending approval."
            )
        )

    approval_request = (
        reject_approval_request(
            approval_request,
            approver,
            comments,
        )
    )

    try:

        discount.status = (
            Discount.Status.REJECTED
        )

        discount.approved_by = None

        discount.approved_at = None

        discount.full_clean()

        discount.save()

    except Exception:

        approval_request.status = (
            ApprovalRequest.Status.PENDING
        )

        approval_request.approver = None

        approval_request.decision_comments = ""

        approval_request.decided_at = None

        approval_request.save()

        raise

    return discount


# ============================================================
# CANCEL DISCOUNT
# ============================================================

def cancel_discount(
    *,
    discount,
    user,
    reason,
):

    discount = (
        Discount.objects.get(
            pk=discount.pk
        )
    )

    reason = (
        reason
        .strip()
        if reason
        else ""
    )

    if not reason:

        raise ValidationError(
            (
                "A cancellation reason "
                "is required."
            )
        )

    if (
        discount.status
        == Discount.Status.CANCELLED
    ):

        raise ValidationError(
            (
                "This discount is "
                "already cancelled."
            )
        )

    if (
        discount.status
        ==
        Discount.Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "A discount cannot be cancelled "
                "while its approval request "
                "is pending."
            )
        )

    if (
        discount.status
        ==
        Discount.Status
        .APPLIED
    ):

        raise ValidationError(
            (
                "An applied discount cannot "
                "be cancelled directly because "
                "its invoice effect would need "
                "to be reversed."
            )
        )

    discount.status = (
        Discount.Status.CANCELLED
    )

    discount.cancellation_reason = (
        reason
    )

    discount.cancelled_at = (
        timezone.now()
    )

    discount.cancelled_by = (
        user
    )

    discount.full_clean()

    discount.save()

    return discount




# ============================================================
# SCHOLARSHIP — CREATE
# ============================================================

def create_scholarship(
    *,
    user,
    scholarship_name,
    student_reference,
    academic_year_reference,
    provider,
    value_type,
    value,
    start_date,
    end_date,
    supporting_document,
    reason,
    requires_approval=True,
):

    scholarship = Scholarship(
        scholarship_name=
            scholarship_name,

        student_reference=
            student_reference,

        academic_year_reference=
            academic_year_reference,

        provider=
            provider,

        value_type=
            value_type,

        value=
            value,

        start_date=
            start_date,

        end_date=
            end_date,

        supporting_document=
            supporting_document,

        reason=
            reason,

        requires_approval=
            requires_approval,

        requested_by=
            user,

        status=
            Scholarship.Status.DRAFT,
    )

    scholarship.full_clean()

    scholarship.save()

    return scholarship


# ============================================================
# SCHOLARSHIP — UPDATE DRAFT
# ============================================================

def update_scholarship(
    *,
    scholarship,
    scholarship_name,
    student_reference,
    academic_year_reference,
    provider,
    value_type,
    value,
    start_date,
    end_date,
    supporting_document,
    reason,
    requires_approval,
):

    scholarship = (
        Scholarship.objects
        .get(
            pk=scholarship.pk
        )
    )

    if (
        scholarship.status
        !=
        Scholarship.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only draft scholarships "
                "can be edited."
            )
        )


    scholarship.scholarship_name = (
        scholarship_name
    )

    scholarship.student_reference = (
        student_reference
    )

    scholarship.academic_year_reference = (
        academic_year_reference
    )

    scholarship.provider = (
        provider
    )

    scholarship.value_type = (
        value_type
    )

    scholarship.value = (
        value
    )

    scholarship.start_date = (
        start_date
    )

    scholarship.end_date = (
        end_date
    )

    scholarship.supporting_document = (
        supporting_document
    )

    scholarship.reason = (
        reason
    )

    scholarship.requires_approval = (
        requires_approval
    )


    scholarship.full_clean()

    scholarship.save()

    return scholarship


# ============================================================
# SCHOLARSHIP — APPROVAL DESCRIPTION
# ============================================================

def _scholarship_approval_description(
    scholarship,
):

    if (
        scholarship.value_type
        ==
        Scholarship
        .ValueType
        .PERCENTAGE
    ):

        value_description = (
            f"{scholarship.value:.2f}%"
        )

    else:

        value_description = (
            f"Fixed amount "
            f"{scholarship.value:.2f}"
        )


    provider_description = (
        scholarship.provider
        if scholarship.provider
        else "Not specified"
    )


    return (
        f"Scholarship "
        f"{scholarship.scholarship_number} "
        f"for student "
        f"{scholarship.student_reference}. "
        f"Scholarship: "
        f"{scholarship.scholarship_name}. "
        f"Academic year: "
        f"{scholarship.academic_year_reference}. "
        f"Provider: "
        f"{provider_description}. "
        f"Value: "
        f"{value_description}."
    )


# ============================================================
# SCHOLARSHIP — SUBMIT
# ============================================================

def submit_scholarship(
    *,
    scholarship,
):

    scholarship = (
        Scholarship.objects
        .get(
            pk=scholarship.pk
        )
    )


    if (
        scholarship.status
        !=
        Scholarship.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only draft scholarships "
                "can be submitted."
            )
        )


    # --------------------------------------------------------
    # DIRECT WORKFLOW
    # --------------------------------------------------------

    if not scholarship.requires_approval:

        scholarship.status = (
            Scholarship.Status.APPROVED
        )

        scholarship.approved_at = (
            timezone.now()
        )

        scholarship.full_clean()

        scholarship.save()

        return scholarship


    # --------------------------------------------------------
    # APPROVAL-CONTROLLED WORKFLOW
    # --------------------------------------------------------

    if scholarship.approval_request_id:

        raise ValidationError(
            (
                "This scholarship already "
                "has an approval request."
            )
        )


    # ApprovalRequest.amount represents a monetary amount.
    # A scholarship percentage therefore does not populate it.
    approval_amount = None


    if (
        scholarship.value_type
        ==
        Scholarship
        .ValueType
        .FIXED_AMOUNT
    ):

        approval_amount = (
            scholarship.value
        )


    approval_request = (
        ApprovalRequest(
            operation_type=
                ApprovalRequest
                .OperationType
                .SCHOLARSHIP,

            title=(
                "Scholarship approval — "
                f"{scholarship.scholarship_number}"
            ),

            description=(
                _scholarship_approval_description(
                    scholarship
                )
            ),

            amount=
                approval_amount,

            related_entity_type=
                "Scholarship",

            related_entity_id=
                str(
                    scholarship.pk
                ),

            requester=
                scholarship.requested_by,

            request_reason=
                scholarship.reason,

            status=
                ApprovalRequest
                .Status
                .REQUESTED,
        )
    )


    approval_request.full_clean()

    approval_request.save()


    try:

        approval_request = (
            submit_approval_request(
                approval_request
            )
        )


        scholarship.approval_request = (
            approval_request
        )

        scholarship.status = (
            Scholarship
            .Status
            .PENDING_APPROVAL
        )


        scholarship.full_clean()

        scholarship.save()


    except Exception:

        # Internal compensating rollback only.
        # The newly-created approval record has never
        # become a valid user-facing financial workflow
        # if scholarship linking fails.
        approval_request.delete()

        raise


    return scholarship


# ============================================================
# SCHOLARSHIP — RESOLVE LINKED APPROVAL
# ============================================================

def get_scholarship_for_approval(
    approval_request,
):

    if (
        approval_request.operation_type
        !=
        ApprovalRequest
        .OperationType
        .SCHOLARSHIP
    ):

        raise ValidationError(
            (
                "This approval request "
                "is not for a scholarship."
            )
        )


    entity_type = (
        approval_request
        .related_entity_type
        or ""
    ).strip()


    entity_id = (
        approval_request
        .related_entity_id
        or ""
    ).strip()


    if (
        entity_type.lower()
        !=
        "scholarship"
        or
        not entity_id
    ):

        raise ValidationError(
            (
                "This approval request "
                "is not linked to a "
                "valid scholarship."
            )
        )


    try:

        scholarship = (
            Scholarship.objects
            .get(
                pk=entity_id
            )
        )

    except Scholarship.DoesNotExist:

        raise ValidationError(
            (
                "The scholarship linked "
                "to this approval request "
                "could not be found."
            )
        )


    if (
        not scholarship.approval_request_id
        or
        str(
            scholarship
            .approval_request_id
        )
        !=
        str(
            approval_request.pk
        )
    ):

        raise ValidationError(
            (
                "The approval request "
                "is not linked to this "
                "scholarship record."
            )
        )


    return scholarship


# ============================================================
# SCHOLARSHIP — APPROVE LINKED APPROVAL
# ============================================================

def approve_scholarship_approval(
    *,
    approval_request,
    approver,
    comments="",
):

    approval_request = (
        ApprovalRequest.objects
        .get(
            pk=approval_request.pk
        )
    )


    scholarship = (
        get_scholarship_for_approval(
            approval_request
        )
    )


    if (
        scholarship.status
        !=
        Scholarship
        .Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "The linked scholarship "
                "is not pending approval."
            )
        )


    approval_request = (
        approve_approval_request(
            approval_request,
            approver,
            comments,
        )
    )


    try:

        scholarship.status = (
            Scholarship.Status.APPROVED
        )

        scholarship.approved_by = (
            approver
        )

        scholarship.approved_at = (
            approval_request.decided_at
            or
            timezone.now()
        )


        scholarship.full_clean()

        scholarship.save()


    except Exception:

        # Restore the generic approval if updating
        # the linked scholarship fails.
        approval_request.status = (
            ApprovalRequest.Status.PENDING
        )

        approval_request.approver = None

        approval_request.decision_comments = ""

        approval_request.decided_at = None

        approval_request.save()

        raise


    return scholarship


# ============================================================
# SCHOLARSHIP — REJECT LINKED APPROVAL
# ============================================================

def reject_scholarship_approval(
    *,
    approval_request,
    approver,
    comments,
):

    approval_request = (
        ApprovalRequest.objects
        .get(
            pk=approval_request.pk
        )
    )


    scholarship = (
        get_scholarship_for_approval(
            approval_request
        )
    )


    if (
        scholarship.status
        !=
        Scholarship
        .Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "The linked scholarship "
                "is not pending approval."
            )
        )


    approval_request = (
        reject_approval_request(
            approval_request,
            approver,
            comments,
        )
    )


    try:

        scholarship.status = (
            Scholarship.Status.REJECTED
        )

        scholarship.approved_by = None

        scholarship.approved_at = None


        scholarship.full_clean()

        scholarship.save()


    except Exception:

        approval_request.status = (
            ApprovalRequest.Status.PENDING
        )

        approval_request.approver = None

        approval_request.decision_comments = ""

        approval_request.decided_at = None

        approval_request.save()

        raise


    return scholarship


# ============================================================
# SCHOLARSHIP — CANCEL
# ============================================================

def cancel_scholarship(
    *,
    scholarship,
    user,
    reason,
):

    scholarship = (
        Scholarship.objects
        .get(
            pk=scholarship.pk
        )
    )


    reason = (
        reason.strip()
        if reason
        else ""
    )


    if not reason:

        raise ValidationError(
            (
                "A cancellation reason "
                "is required."
            )
        )


    if (
        scholarship.status
        ==
        Scholarship.Status.CANCELLED
    ):

        raise ValidationError(
            (
                "This scholarship "
                "is already cancelled."
            )
        )


    if (
        scholarship.status
        ==
        Scholarship
        .Status
        .PENDING_APPROVAL
    ):

        raise ValidationError(
            (
                "A scholarship cannot "
                "be cancelled while its "
                "approval request is pending."
            )
        )


    if (
        scholarship.status
        ==
        Scholarship.Status.APPLIED
    ):

        raise ValidationError(
            (
                "An applied scholarship "
                "cannot be cancelled directly "
                "because its effect on the "
                "student's financial liability "
                "would need to be reversed."
            )
        )


    scholarship.status = (
        Scholarship.Status.CANCELLED
    )

    scholarship.cancellation_reason = (
        reason
    )

    scholarship.cancelled_at = (
        timezone.now()
    )

    scholarship.cancelled_by = (
        user
    )


    scholarship.full_clean()

    scholarship.save()


    return scholarship
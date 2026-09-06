from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from .models import PaymentReminder


# ============================================================
# DELIVERY BACKEND CLASSIFICATION
# ============================================================

NON_EXTERNAL_EMAIL_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
}


# ============================================================
# DELIVERY CAPABILITY
# ============================================================

def email_delivery_ready():
    """
    Return True only when the configured Django email backend
    appears capable of real external delivery.

    The current EduFinance project uses ConsoleEmailBackend,
    which prints email content to the terminal and therefore
    must not be treated as successful external delivery.
    """

    backend = (
        getattr(
            settings,
            "EMAIL_BACKEND",
            "",
        )
        or ""
    ).strip()

    if not backend:
        return False

    return (
        backend
        not in NON_EXTERNAL_EMAIL_BACKENDS
    )


def in_system_delivery_ready():
    """
    Student/Guardian in-system reminders are not yet available.

    accounts.Notification targets settings.AUTH_USER_MODEL,
    while the current Student and Guardian models do not have
    an authenticated portal-user relationship.

    Returning False prevents EduFinance from falsely claiming
    that a Student or Guardian received an internal notification.
    """

    return False


# ============================================================
# RECIPIENT SNAPSHOT
# ============================================================

def _resolve_recipient_snapshot(
    *,
    student,
    guardian=None,
    recipient_name="",
    recipient_email="",
):
    """
    Resolve immutable recipient snapshot values.

    Priority:
        explicit snapshot
        -> guardian
        -> student
    """

    resolved_name = (
        recipient_name
        or ""
    ).strip()

    resolved_email = (
        recipient_email
        or ""
    ).strip()


    if guardian:

        if not resolved_name:

            resolved_name = (
                guardian.full_name
                or ""
            ).strip()

        if not resolved_email:

            resolved_email = (
                guardian.email
                or ""
            ).strip()


    elif student:

        if not resolved_name:

            resolved_name = (
                student.full_name
                or ""
            ).strip()

        if not resolved_email:

            resolved_email = (
                student.email
                or ""
            ).strip()


    return (
        resolved_name,
        resolved_email,
    )


# ============================================================
# CREATE
# ============================================================

def create_payment_reminder(
    *,
    user,
    student,
    guardian=None,
    invoice_reference,
    amount_due,
    due_date,
    reminder_date,
    delivery_method,
    recipient_name="",
    recipient_email="",
    subject,
    message,
):
    """
    Create a Draft reminder.

    Creation does not send anything.
    """

    (
        recipient_name,
        recipient_email,
    ) = _resolve_recipient_snapshot(
        student=student,
        guardian=guardian,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
    )


    reminder = PaymentReminder(
        student=student,
        guardian=guardian,

        invoice_reference=(
            invoice_reference
            or ""
        ).strip(),

        amount_due=amount_due,
        due_date=due_date,
        reminder_date=reminder_date,

        delivery_method=delivery_method,

        recipient_name=recipient_name,
        recipient_email=recipient_email,

        subject=(
            subject
            or ""
        ).strip(),

        message=(
            message
            or ""
        ).strip(),

        status=PaymentReminder.Status.DRAFT,

        created_by=user,
    )


    reminder.full_clean()

    reminder.save()

    return reminder


# ============================================================
# UPDATE
# ============================================================

def update_payment_reminder(
    reminder,
    *,
    student,
    guardian=None,
    invoice_reference,
    amount_due,
    due_date,
    reminder_date,
    delivery_method,
    recipient_name="",
    recipient_email="",
    subject,
    message,
):
    """
    Update a Draft reminder.

    Sent, Failed and Cancelled reminder records are historical
    and cannot be edited.
    """

    if (
        reminder.status
        != PaymentReminder.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only payment reminders in Draft "
                "status can be edited."
            )
        )


    (
        recipient_name,
        recipient_email,
    ) = _resolve_recipient_snapshot(
        student=student,
        guardian=guardian,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
    )


    reminder.student = student
    reminder.guardian = guardian

    reminder.invoice_reference = (
        invoice_reference
        or ""
    ).strip()

    reminder.amount_due = amount_due

    reminder.due_date = due_date

    reminder.reminder_date = (
        reminder_date
    )

    reminder.delivery_method = (
        delivery_method
    )

    reminder.recipient_name = (
        recipient_name
    )

    reminder.recipient_email = (
        recipient_email
    )

    reminder.subject = (
        subject
        or ""
    ).strip()

    reminder.message = (
        message
        or ""
    ).strip()


    reminder.full_clean()

    reminder.save()

    return reminder


# ============================================================
# MARK FAILED
# ============================================================

def _mark_payment_reminder_failed(
    reminder,
    reason,
):
    """
    Preserve a failed delivery attempt.

    A failed reminder remains in the financial audit history.
    """

    failure_reason = (
        reason
        or
        "Reminder delivery failed."
    ).strip()


    reminder.status = (
        PaymentReminder.Status.FAILED
    )

    reminder.failure_reason = (
        failure_reason
    )

    reminder.sent_at = None
    reminder.sent_by = None

    reminder.full_clean()

    reminder.save()

    return reminder


# ============================================================
# EMAIL DELIVERY
# ============================================================

def _send_email_reminder(
    reminder,
):
    """
    Attempt actual external email delivery.

    Console, local-memory, dummy and file-based Django backends
    are intentionally rejected because they do not represent
    real recipient delivery.
    """

    if not email_delivery_ready():

        raise ValidationError(
            (
                "External email delivery is not configured. "
                "The current Django email backend does not "
                "deliver messages to real recipients."
            )
        )


    recipient_email = (
        reminder.recipient_email
        or ""
    ).strip()


    if not recipient_email:

        raise ValidationError(
            (
                "This payment reminder does not "
                "have a recipient email address."
            )
        )


    from_email = (
        getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            "",
        )
        or
        "webmaster@localhost"
    )


    sent_count = send_mail(
        subject=reminder.subject,
        message=reminder.message,
        from_email=from_email,
        recipient_list=[
            recipient_email,
        ],
        fail_silently=False,
    )


    if sent_count != 1:

        raise ValidationError(
            (
                "The email backend did not confirm "
                "successful reminder delivery."
            )
        )


# ============================================================
# IN-SYSTEM DELIVERY
# ============================================================

def _send_in_system_reminder(
    reminder,
):
    """
    Student/Guardian internal delivery guard.

    The existing Notification model belongs to authenticated
    application users. Student and Guardian currently have no
    safe mapping to those users.
    """

    if not in_system_delivery_ready():

        raise ValidationError(
            (
                "In-system reminder delivery is not available "
                "yet because the selected Student or Guardian "
                "is not linked to an authenticated portal user."
            )
        )


    # --------------------------------------------------------
    # FUTURE INTEGRATION POINT
    #
    # Once a Student/Guardian -> authenticated user relation is
    # implemented, create accounts.Notification here.
    # --------------------------------------------------------

    raise ValidationError(
        (
            "In-system reminder delivery has not "
            "yet been integrated."
        )
    )


# ============================================================
# SEND
# ============================================================

def send_payment_reminder(
    reminder,
    user,
):
    """
    Attempt delivery of one Draft reminder.

    Successful delivery:
        Draft -> Sent

    Failed delivery:
        Draft -> Failed

    A reminder is never marked Sent unless the selected
    delivery mechanism confirms successful delivery.
    """

    if (
        reminder.status
        != PaymentReminder.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only payment reminders in Draft "
                "status can be sent."
            )
        )


    try:

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        if (
            reminder.delivery_method
            ==
            PaymentReminder
            .DeliveryMethod
            .EMAIL
        ):

            _send_email_reminder(
                reminder
            )


        # ----------------------------------------------------
        # IN-SYSTEM
        # ----------------------------------------------------

        elif (
            reminder.delivery_method
            ==
            PaymentReminder
            .DeliveryMethod
            .IN_SYSTEM
        ):

            _send_in_system_reminder(
                reminder
            )


        # ----------------------------------------------------
        # UNKNOWN METHOD
        # ----------------------------------------------------

        else:

            raise ValidationError(
                (
                    "Unsupported payment reminder "
                    "delivery method."
                )
            )


    except ValidationError as error:

        reason = (
            "; ".join(
                error.messages
            )
            if getattr(
                error,
                "messages",
                None,
            )
            else str(error)
        )


        _mark_payment_reminder_failed(
            reminder,
            reason,
        )


        raise ValidationError(
            reason
        )


    except Exception as error:

        reason = (
            "Reminder delivery failed: "
            f"{error}"
        )


        _mark_payment_reminder_failed(
            reminder,
            reason,
        )


        raise ValidationError(
            reason
        )


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    reminder.status = (
        PaymentReminder.Status.SENT
    )

    reminder.sent_at = (
        timezone.now()
    )

    reminder.sent_by = user

    reminder.failure_reason = ""

    reminder.full_clean()

    reminder.save()

    return reminder


# ============================================================
# CANCEL
# ============================================================

def cancel_payment_reminder(
    reminder,
    *,
    user,
    reason,
):
    """
    Cancel a Draft reminder without deleting it.

    Financial communication history remains auditable.
    """

    if (
        reminder.status
        != PaymentReminder.Status.DRAFT
    ):

        raise ValidationError(
            (
                "Only payment reminders in Draft "
                "status can be cancelled."
            )
        )


    cancellation_reason = (
        reason
        or ""
    ).strip()


    if not cancellation_reason:

        raise ValidationError(
            (
                "A cancellation reason "
                "is required."
            )
        )


    reminder.status = (
        PaymentReminder.Status.CANCELLED
    )

    reminder.cancellation_reason = (
        cancellation_reason
    )

    reminder.cancelled_at = (
        timezone.now()
    )

    reminder.cancelled_by = user

    reminder.full_clean()

    reminder.save()

    return reminder
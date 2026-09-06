from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from school_config.models import School
from students.models import (
    Guardian,
    Student,
)

from .models import PaymentReminder
from .payment_reminder_forms import (
    PaymentReminderForm,
)
from .payment_reminder_services import (
    cancel_payment_reminder,
    create_payment_reminder,
    email_delivery_ready,
    in_system_delivery_ready,
    send_payment_reminder,
    update_payment_reminder,
)


# ============================================================
# SCHOOL CURRENCY
# ============================================================

def get_school_currency():
    """
    Return the configured school currency.
    """

    school = (
        School.objects
        .first()
    )

    if (
        school
        and
        school.default_currency
    ):
        return school.default_currency

    return "USD"


# ============================================================
# VALIDATION MESSAGE
# ============================================================

def _validation_message(
    error,
):
    """
    Convert Django ValidationError into one readable message.
    """

    if hasattr(
        error,
        "message_dict",
    ):

        parts = []

        for field, errors in (
            error.message_dict.items()
        ):

            for message in errors:

                parts.append(
                    str(message)
                )

        if parts:

            return " ".join(
                parts
            )

    if getattr(
        error,
        "messages",
        None,
    ):

        return " ".join(
            str(message)
            for message in error.messages
        )

    return str(error)


# ============================================================
# SEARCH HELPERS
# ============================================================

def _matching_student_ids(
    search,
):
    """
    Search students separately to avoid relying on relational
    joins in MongoDB-backed queries.
    """

    if not search:
        return []

    return list(
        Student.objects
        .filter(
            Q(
                student_number__icontains=
                    search
            )
            |
            Q(
                admission_number__icontains=
                    search
            )
            |
            Q(
                first_name__icontains=
                    search
            )
            |
            Q(
                last_name__icontains=
                    search
            )
            |
            Q(
                email__icontains=
                    search
            )
        )
        .values_list(
            "pk",
            flat=True,
        )
    )


def _matching_guardian_ids(
    search,
):
    """
    Search guardians separately to keep the reminder query
    dependency-safe for MongoDB.
    """

    if not search:
        return []

    return list(
        Guardian.objects
        .filter(
            Q(
                first_name__icontains=
                    search
            )
            |
            Q(
                last_name__icontains=
                    search
            )
            |
            Q(
                email__icontains=
                    search
            )
            |
            Q(
                phone__icontains=
                    search
            )
        )
        .values_list(
            "pk",
            flat=True,
        )
    )


# ============================================================
# LIST
# ============================================================

@login_required
def payment_reminder_list(
    request,
):

    search = (
        request.GET
        .get(
            "search",
            "",
        )
        .strip()
    )

    status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    delivery_method = (
        request.GET
        .get(
            "delivery_method",
            "",
        )
        .strip()
    )


    # --------------------------------------------------------
    # BASE QUERYSET
    # --------------------------------------------------------

    reminders = (
        PaymentReminder.objects
        .all()
        .order_by(
            "-created_at"
        )
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        student_ids = (
            _matching_student_ids(
                search
            )
        )

        guardian_ids = (
            _matching_guardian_ids(
                search
            )
        )


        search_query = (
            Q(
                reminder_number__icontains=
                    search
            )
            |
            Q(
                invoice_reference__icontains=
                    search
            )
            |
            Q(
                recipient_name__icontains=
                    search
            )
            |
            Q(
                recipient_email__icontains=
                    search
            )
            |
            Q(
                subject__icontains=
                    search
            )
        )


        if student_ids:

            search_query |= Q(
                student_id__in=
                    student_ids
            )


        if guardian_ids:

            search_query |= Q(
                guardian_id__in=
                    guardian_ids
            )


        reminders = (
            reminders.filter(
                search_query
            )
        )


    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    valid_statuses = {
        value
        for value, label
        in PaymentReminder
        .Status
        .choices
    }


    if status in valid_statuses:

        reminders = (
            reminders.filter(
                status=status
            )
        )

    else:

        status = ""


    # --------------------------------------------------------
    # DELIVERY METHOD FILTER
    # --------------------------------------------------------

    valid_delivery_methods = {
        value
        for value, label
        in PaymentReminder
        .DeliveryMethod
        .choices
    }


    if (
        delivery_method
        in valid_delivery_methods
    ):

        reminders = (
            reminders.filter(
                delivery_method=
                    delivery_method
            )
        )

    else:

        delivery_method = ""


    # --------------------------------------------------------
    # KPI DATA
    #
    # KPIs use the complete reminder register rather than the
    # filtered table.
    # --------------------------------------------------------

    all_reminders = (
        PaymentReminder.objects
        .all()
    )


    total_count = (
        all_reminders.count()
    )


    draft_count = (
        all_reminders
        .filter(
            status=
                PaymentReminder
                .Status
                .DRAFT
        )
        .count()
    )


    sent_count = (
        all_reminders
        .filter(
            status=
                PaymentReminder
                .Status
                .SENT
        )
        .count()
    )


    failed_count = (
        all_reminders
        .filter(
            status=
                PaymentReminder
                .Status
                .FAILED
        )
        .count()
    )


    cancelled_count = (
        all_reminders
        .filter(
            status=
                PaymentReminder
                .Status
                .CANCELLED
        )
        .count()
    )


    email_count = (
        all_reminders
        .filter(
            delivery_method=
                PaymentReminder
                .DeliveryMethod
                .EMAIL
        )
        .count()
    )


    in_system_count = (
        all_reminders
        .filter(
            delivery_method=
                PaymentReminder
                .DeliveryMethod
                .IN_SYSTEM
        )
        .count()
    )


    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginator = Paginator(
        reminders,
        15,
    )


    page_obj = (
        paginator.get_page(
            request.GET.get(
                "page"
            )
        )
    )


    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "page_obj":
            page_obj,

        "reminders":
            page_obj.object_list,

        "search":
            search,

        "selected_status":
            status,

        "selected_delivery_method":
            delivery_method,

        "status_choices":
            PaymentReminder
            .Status
            .choices,

        "delivery_method_choices":
            PaymentReminder
            .DeliveryMethod
            .choices,

        "total_count":
            total_count,

        "draft_count":
            draft_count,

        "sent_count":
            sent_count,

        "failed_count":
            failed_count,

        "cancelled_count":
            cancelled_count,

        "email_count":
            email_count,

        "in_system_count":
            in_system_count,

        "filtered_count":
            paginator.count,

        "currency_code":
            get_school_currency(),

        "email_delivery_ready":
            email_delivery_ready(),

        "in_system_delivery_ready":
            in_system_delivery_ready(),
    }


    return render(
        request,
        (
            "payables/"
            "payment_reminder_list.html"
        ),
        context,
    )


# ============================================================
# CREATE
# ============================================================

@login_required
def payment_reminder_create(
    request,
):

    if request.method == "POST":

        form = PaymentReminderForm(
            request.POST
        )


        if form.is_valid():

            try:

                reminder = (
                    create_payment_reminder(
                        user=request.user,

                        student=
                            form.cleaned_data[
                                "student"
                            ],

                        guardian=
                            form.cleaned_data.get(
                                "guardian"
                            ),

                        invoice_reference=
                            form.cleaned_data[
                                "invoice_reference"
                            ],

                        amount_due=
                            form.cleaned_data[
                                "amount_due"
                            ],

                        due_date=
                            form.cleaned_data[
                                "due_date"
                            ],

                        reminder_date=
                            form.cleaned_data[
                                "reminder_date"
                            ],

                        delivery_method=
                            form.cleaned_data[
                                "delivery_method"
                            ],

                        recipient_name=
                            form.cleaned_data.get(
                                "recipient_name",
                                "",
                            ),

                        recipient_email=
                            form.cleaned_data.get(
                                "recipient_email",
                                "",
                            ),

                        subject=
                            form.cleaned_data[
                                "subject"
                            ],

                        message=
                            form.cleaned_data[
                                "message"
                            ],
                    )
                )


                messages.success(
                    request,
                    (
                        f"{reminder.reminder_number} "
                        "was created as a draft."
                    ),
                )


                return redirect(
                    "payables:"
                    "payment_reminder_detail",
                    pk=reminder.pk,
                )


            except ValidationError as error:

                form.add_error(
                    None,
                    _validation_message(
                        error
                    ),
                )


    else:

        form = (
            PaymentReminderForm()
        )


    return render(
        request,
        (
            "payables/"
            "payment_reminder_form.html"
        ),
        {
            "form":
                form,

            "page_title":
                "Create Payment Reminder",

            "page_subtitle":
                (
                    "Prepare a financial reminder "
                    "for a student or guardian."
                ),

            "submit_text":
                "Create Draft Reminder",

            "is_edit":
                False,

            "currency_code":
                get_school_currency(),

            "email_delivery_ready":
                email_delivery_ready(),

            "in_system_delivery_ready":
                in_system_delivery_ready(),
        },
    )


# ============================================================
# DETAIL
# ============================================================

@login_required
def payment_reminder_detail(
    request,
    pk,
):

    reminder = (
        get_object_or_404(
            PaymentReminder,
            pk=pk,
        )
    )


    return render(
        request,
        (
            "payables/"
            "payment_reminder_detail.html"
        ),
        {
            "reminder":
                reminder,

            "currency_code":
                get_school_currency(),

            "email_delivery_ready":
                email_delivery_ready(),

            "in_system_delivery_ready":
                in_system_delivery_ready(),
        },
    )


# ============================================================
# EDIT
# ============================================================

@login_required
def payment_reminder_edit(
    request,
    pk,
):

    reminder = (
        get_object_or_404(
            PaymentReminder,
            pk=pk,
        )
    )


    # --------------------------------------------------------
    # HISTORICAL RECORD GUARD
    # --------------------------------------------------------

    if (
        reminder.status
        != PaymentReminder.Status.DRAFT
    ):

        messages.error(
            request,
            (
                "Only payment reminders in Draft "
                "status can be edited."
            ),
        )

        return redirect(
            "payables:"
            "payment_reminder_detail",
            pk=reminder.pk,
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = PaymentReminderForm(
            request.POST,
            instance=reminder,
        )


        if form.is_valid():

            try:

                reminder = (
                    update_payment_reminder(
                        reminder,

                        student=
                            form.cleaned_data[
                                "student"
                            ],

                        guardian=
                            form.cleaned_data.get(
                                "guardian"
                            ),

                        invoice_reference=
                            form.cleaned_data[
                                "invoice_reference"
                            ],

                        amount_due=
                            form.cleaned_data[
                                "amount_due"
                            ],

                        due_date=
                            form.cleaned_data[
                                "due_date"
                            ],

                        reminder_date=
                            form.cleaned_data[
                                "reminder_date"
                            ],

                        delivery_method=
                            form.cleaned_data[
                                "delivery_method"
                            ],

                        recipient_name=
                            form.cleaned_data.get(
                                "recipient_name",
                                "",
                            ),

                        recipient_email=
                            form.cleaned_data.get(
                                "recipient_email",
                                "",
                            ),

                        subject=
                            form.cleaned_data[
                                "subject"
                            ],

                        message=
                            form.cleaned_data[
                                "message"
                            ],
                    )
                )


                messages.success(
                    request,
                    (
                        f"{reminder.reminder_number} "
                        "was updated successfully."
                    ),
                )


                return redirect(
                    "payables:"
                    "payment_reminder_detail",
                    pk=reminder.pk,
                )


            except ValidationError as error:

                form.add_error(
                    None,
                    _validation_message(
                        error
                    ),
                )


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    else:

        form = PaymentReminderForm(
            instance=reminder
        )


    return render(
        request,
        (
            "payables/"
            "payment_reminder_form.html"
        ),
        {
            "form":
                form,

            "reminder":
                reminder,

            "page_title":
                "Edit Payment Reminder",

            "page_subtitle":
                (
                    "Update this draft before "
                    "attempting delivery."
                ),

            "submit_text":
                "Save Reminder",

            "is_edit":
                True,

            "currency_code":
                get_school_currency(),

            "email_delivery_ready":
                email_delivery_ready(),

            "in_system_delivery_ready":
                in_system_delivery_ready(),
        },
    )


# ============================================================
# SEND
# ============================================================

@login_required
@require_POST
def payment_reminder_send(
    request,
    pk,
):

    reminder = (
        get_object_or_404(
            PaymentReminder,
            pk=pk,
        )
    )


    try:

        reminder = (
            send_payment_reminder(
                reminder,
                request.user,
            )
        )


        messages.success(
            request,
            (
                f"{reminder.reminder_number} "
                "was delivered successfully."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            _validation_message(
                error
            ),
        )


    return redirect(
        "payables:"
        "payment_reminder_detail",
        pk=reminder.pk,
    )


# ============================================================
# CANCEL
# ============================================================

@login_required
@require_POST
def payment_reminder_cancel(
    request,
    pk,
):

    reminder = (
        get_object_or_404(
            PaymentReminder,
            pk=pk,
        )
    )


    reason = (
        request.POST
        .get(
            "cancellation_reason",
            "",
        )
        .strip()
    )


    try:

        reminder = (
            cancel_payment_reminder(
                reminder,
                user=request.user,
                reason=reason,
            )
        )


        messages.success(
            request,
            (
                f"{reminder.reminder_number} "
                "was cancelled."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            _validation_message(
                error
            ),
        )


    return redirect(
        "payables:"
        "payment_reminder_detail",
        pk=reminder.pk,
    )
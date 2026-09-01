from datetime import timedelta
from decimal import Decimal


from django.contrib.auth import get_user_model

from school_config.models import School

from django.core.exceptions import ValidationError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ExpenseCategoryForm,
    SupplierForm,
    SupplierBillForm,
    SupplierPaymentForm,
    ExpenseForm,
    EmployeeFinancialProfileForm,
    EmployeeFinancialTransactionForm,
    DiscountForm,
)

from .models import (
    ExpenseCategory,
    Supplier,
    SupplierBill,
    SupplierPayment,
    Expense,
    EmployeeFinancialProfile,
    EmployeeFinancialTransaction,
    Discount,
)

from .services import (
    create_supplier_payment,
    void_supplier_payment,
    void_expense,
    void_employee_financial_transaction,
    create_discount,
    update_discount,
    submit_discount,
    cancel_discount,
)


from .forms import ApprovalRequestForm
from .models import ApprovalRequest
from .services import (
    approve_approval_request,
    process_approval_request,
    reject_approval_request,
    submit_approval_request,
    approve_discount_approval,
    reject_discount_approval,
)


def get_school_currency():

    school = (
        School.objects
        .first()
    )

    if (
        school
        and
        school.default_currency
    ):

        return (
            school.default_currency
        )

    return "USD"


def _add_validation_error_to_form(
    form,
    error,
):

    if hasattr(
        error,
        "message_dict",
    ):

        for field, errors in error.message_dict.items():

            form_field = (
                field
                if field in form.fields
                else None
            )

            for message in errors:
                form.add_error(
                    form_field,
                    message,
                )

        return

    for message in error.messages:
        form.add_error(
            None,
            message,
        )




@login_required
def expense_category_list(request):
    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    categories = ExpenseCategory.objects.all()

    if search:
        categories = categories.filter(
            Q(name__icontains=search)
            | Q(
                description__icontains=search
            )
        )

    if status == "active":
        categories = categories.filter(
            is_active=True
        )

    elif status == "inactive":
        categories = categories.filter(
            is_active=False
        )

    context = {
        "categories": categories,
        "search": search,
        "status": status,

        "total_categories": (
            ExpenseCategory.objects.count()
        ),

        "active_categories": (
            ExpenseCategory.objects.filter(
                is_active=True
            ).count()
        ),

        "inactive_categories": (
            ExpenseCategory.objects.filter(
                is_active=False
            ).count()
        ),
    }

    return render(
        request,
        "payables/expense_category_list.html",
        context,
    )


@login_required
def expense_category_create(request):

    if request.method == "POST":
        form = ExpenseCategoryForm(
            request.POST
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                (
                    f'"{category.name}" '
                    "was created successfully."
                ),
            )

            return redirect(
                "payables:expense_category_list"
            )

    else:
        form = ExpenseCategoryForm()

    return render(
        request,
        "payables/expense_category_form.html",
        {
            "form": form,
            "page_title": (
                "Add Expense Category"
            ),
            "submit_text": (
                "Create Category"
            ),
            "is_edit": False,
        },
    )


@login_required
def expense_category_edit(
    request,
    pk,
):

    category = get_object_or_404(
        ExpenseCategory,
        pk=pk,
    )

    if request.method == "POST":

        form = ExpenseCategoryForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():

            category = form.save()

            messages.success(
                request,
                (
                    f'"{category.name}" '
                    "was updated successfully."
                ),
            )

            return redirect(
                "payables:expense_category_list"
            )

    else:
        form = ExpenseCategoryForm(
            instance=category
        )

    return render(
        request,
        "payables/expense_category_form.html",
        {
            "form": form,
            "category": category,
            "page_title": (
                "Edit Expense Category"
            ),
            "submit_text": (
                "Save Changes"
            ),
            "is_edit": True,
        },
    )


@login_required
@require_POST
def expense_category_toggle(
    request,
    pk,
):

    category = get_object_or_404(
        ExpenseCategory,
        pk=pk,
    )

    category.is_active = (
        not category.is_active
    )

    category.save()

    if category.is_active:
        message = (
            f'"{category.name}" '
            "was activated."
        )
    else:
        message = (
            f'"{category.name}" '
            "was deactivated."
        )

    messages.success(
        request,
        message,
    )

    return redirect(
        "payables:expense_category_list"
    )


@login_required
def supplier_list(request):
    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    suppliers = Supplier.objects.all()

    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search)
            | Q(contact_person__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    if status == "active":
        suppliers = suppliers.filter(
            is_active=True
        )

    elif status == "inactive":
        suppliers = suppliers.filter(
            is_active=False
        )

    context = {
        "suppliers": suppliers,
        "search": search,
        "status": status,

        "total_suppliers": (
            Supplier.objects.count()
        ),

        "active_suppliers": (
            Supplier.objects.filter(
                is_active=True
            ).count()
        ),

        "inactive_suppliers": (
            Supplier.objects.filter(
                is_active=False
            ).count()
        ),
    }

    return render(
        request,
        "payables/supplier_list.html",
        context,
    )


@login_required
def supplier_create(request):

    if request.method == "POST":
        form = SupplierForm(
            request.POST
        )

        if form.is_valid():
            supplier = form.save()

            messages.success(
                request,
                f'"{supplier.name}" was created successfully.',
            )

            return redirect(
                "payables:supplier_list"
            )

    else:
        form = SupplierForm()

    return render(
        request,
        "payables/supplier_form.html",
        {
            "form": form,
            "page_title": "Add Supplier",
            "submit_text": "Create Supplier",
            "is_edit": False,
        },
    )


@login_required
def supplier_edit(
    request,
    pk,
):

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    if request.method == "POST":

        form = SupplierForm(
            request.POST,
            instance=supplier,
        )

        if form.is_valid():
            supplier = form.save()

            messages.success(
                request,
                f'"{supplier.name}" was updated successfully.',
            )

            return redirect(
                "payables:supplier_detail",
                pk=supplier.pk,
            )

    else:
        form = SupplierForm(
            instance=supplier
        )

    return render(
        request,
        "payables/supplier_form.html",
        {
            "form": form,
            "supplier": supplier,
            "page_title": "Edit Supplier",
            "submit_text": "Save Changes",
            "is_edit": True,
        },
    )


@login_required
def supplier_detail(
    request,
    pk,
):

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    return render(
        request,
        "payables/supplier_detail.html",
        {
            "supplier": supplier,
        },
    )


@login_required
@require_POST
def supplier_toggle(
    request,
    pk,
):

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    supplier.is_active = (
        not supplier.is_active
    )

    supplier.save()

    messages.success(
        request,
        (
            f'"{supplier.name}" was '
            f'{"activated" if supplier.is_active else "deactivated"}.'
        ),
    )

    return redirect(
        "payables:supplier_list"
    )


# ============================================================
# SUPPLIER BILL HELPERS
# ============================================================

def _refresh_supplier_bill_overdue_statuses():

    today = timezone.localdate()

    SupplierBill.objects.filter(
        due_date__lt=today,
        remaining_amount__gt=0,
        status__in=[
            SupplierBill.Status.UNPAID,
            SupplierBill.Status.PARTIALLY_PAID,
        ],
    ).update(
        status=SupplierBill.Status.OVERDUE
    )


# ============================================================
# SUPPLIER BILL LIST
# ============================================================

@login_required
def supplier_bill_list(request):

    _refresh_supplier_bill_overdue_statuses()

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    status = (
        request.GET.get(
            "status",
            ""
        )
        .strip()
    )

    supplier_id = (
        request.GET.get(
            "supplier",
            ""
        )
        .strip()
    )

    bills = SupplierBill.objects.all()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        matching_supplier_ids = list(
            Supplier.objects.filter(
                name__icontains=search
            ).values_list(
                "pk",
                flat=True,
            )
        )

        bills = bills.filter(
            Q(
                bill_number__icontains=search
            )
            |
            Q(
                description__icontains=search
            )
            |
            Q(
                supplier_id__in=matching_supplier_ids
            )
        )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status:

        bills = bills.filter(
            status=status
        )

    # --------------------------------------------------------
    # SUPPLIER FILTER
    # --------------------------------------------------------

    if supplier_id:

        bills = bills.filter(
            supplier_id=supplier_id
        )

    bills = bills.order_by(
        "-bill_date",
        "-created_at",
    )

    # --------------------------------------------------------
    # KPI CALCULATIONS
    # --------------------------------------------------------

    all_bills = list(
        SupplierBill.objects.all()
    )

    financial_bills = [
        bill
        for bill in all_bills
        if bill.status
        != SupplierBill.Status.CANCELLED
    ]

    total_billed = sum(
        (
            bill.total_amount
            for bill in financial_bills
        ),
        Decimal("0.00"),
    )

    outstanding_amount = sum(
        (
            bill.remaining_amount
            for bill in financial_bills
        ),
        Decimal("0.00"),
    )

    overdue_count = sum(
        1
        for bill in financial_bills
        if bill.status
        == SupplierBill.Status.OVERDUE
    )

    today = timezone.localdate()

    due_soon_limit = (
        today
        + timedelta(days=7)
    )

    due_soon_count = sum(
        1
        for bill in financial_bills
        if (
            bill.remaining_amount > 0
            and bill.due_date >= today
            and bill.due_date <= due_soon_limit
        )
    )

    context = {

        "bills": bills,

        "suppliers":
            Supplier.objects.order_by(
                "name"
            ),

        "search": search,

        "status": status,

        "selected_supplier":
            supplier_id,

        "status_choices":
            SupplierBill.Status.choices,

        "total_bills":
            len(all_bills),

        "total_billed":
            total_billed,

        "outstanding_amount":
            outstanding_amount,

        "overdue_count":
            overdue_count,

        "due_soon_count":
            due_soon_count,

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        "payables/supplier_bill_list.html",
        context,
    )


# ============================================================
# CREATE SUPPLIER BILL
# ============================================================

@login_required
def supplier_bill_create(request):

    if request.method == "POST":

        form = SupplierBillForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            try:

                bill = form.save()

            except ValidationError as error:

                _add_validation_error_to_form(
                    form,
                    error,
                )

            else:

                messages.success(
                    request,
                    (
                        f"Supplier bill "
                        f"{bill.bill_number} "
                        f"was created successfully."
                    ),
                )

                return redirect(
                    "payables:supplier_bill_detail",
                    pk=bill.pk,
                )

    else:

        form = SupplierBillForm(
            initial={
                "bill_date":
                    timezone.localdate(),
            }
        )

    context = {

        "form": form,

        "page_title":
            "Create Supplier Bill",

        "submit_text":
            "Create Bill",

        "is_edit":
            False,

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        "payables/supplier_bill_form.html",
        context,
    )


# ============================================================
# EDIT SUPPLIER BILL
# ============================================================

@login_required
def supplier_bill_edit(
    request,
    pk,
):

    bill = get_object_or_404(
        SupplierBill,
        pk=pk,
    )

    if request.method == "POST":

        form = SupplierBillForm(
            request.POST,
            request.FILES,
            instance=bill,
        )

        if form.is_valid():

            try:

                bill = form.save()

            except ValidationError as error:

                _add_validation_error_to_form(
                    form,
                    error,
                )

            else:

                messages.success(
                    request,
                    (
                        f"Supplier bill "
                        f"{bill.bill_number} "
                        f"was updated successfully."
                    ),
                )

                return redirect(
                    "payables:supplier_bill_detail",
                    pk=bill.pk,
                )

    else:

        form = SupplierBillForm(
            instance=bill
        )

    context = {

        "form": form,

        "bill": bill,

        "page_title":
            "Edit Supplier Bill",

        "submit_text":
            "Save Changes",

        "is_edit":
            True,

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        "payables/supplier_bill_form.html",
        context,
    )


# ============================================================
# SUPPLIER BILL DETAIL
# ============================================================

@login_required
def supplier_bill_detail(
    request,
    pk,
):

    _refresh_supplier_bill_overdue_statuses()

    bill = get_object_or_404(
        SupplierBill,
        pk=pk,
    )

    return render(
        request,
        "payables/supplier_bill_detail.html",
        {
            "bill": bill,
            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# CANCEL / REOPEN BILL
# ============================================================

@login_required
def supplier_bill_toggle_cancel(
    request,
    pk,
):

    bill = get_object_or_404(
        SupplierBill,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "payables:supplier_bill_detail",
            pk=bill.pk,
        )

    if (
        bill.status
        == SupplierBill.Status.CANCELLED
    ):

        bill.status = (
            SupplierBill.Status.UNPAID
        )

        bill.save()

        messages.success(
            request,
            (
                f"Supplier bill "
                f"{bill.bill_number} "
                f"was reopened."
            ),
        )

    else:

        bill.status = (
            SupplierBill.Status.CANCELLED
        )

        bill.save()

        messages.success(
            request,
            (
                f"Supplier bill "
                f"{bill.bill_number} "
                f"was cancelled."
            ),
        )

    return redirect(
        "payables:supplier_bill_detail",
        pk=bill.pk,
    )




# ============================================================
# SUPPLIER PAYMENT LIST
# ============================================================

@login_required
def supplier_payment_list(request):

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    method = (
        request.GET.get(
            "method",
            ""
        )
        .strip()
    )

    status = (
        request.GET.get(
            "status",
            ""
        )
        .strip()
    )

    supplier_id = (
        request.GET.get(
            "supplier",
            ""
        )
        .strip()
    )

    payments = (
        SupplierPayment.objects.all()
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        supplier_ids = list(
            Supplier.objects.filter(
                name__icontains=search
            ).values_list(
                "pk",
                flat=True,
            )
        )

        matching_bill_ids = list(
            SupplierBill.objects.filter(
                Q(
                    bill_number__icontains=
                        search
                )
                |
                Q(
                    supplier_id__in=
                        supplier_ids
                )
            ).values_list(
                "pk",
                flat=True,
            )
        )

        payments = payments.filter(
            Q(
                payment_number__icontains=
                    search
            )
            |
            Q(
                reference__icontains=
                    search
            )
            |
            Q(
                bill_id__in=
                    matching_bill_ids
            )
        )

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    if method:

        payments = payments.filter(
            payment_method=method
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if status:

        payments = payments.filter(
            status=status
        )

    # --------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------

    if supplier_id:

        payments = payments.filter(
            supplier_id=supplier_id
        )

    payments = payments.order_by(
        "-payment_date",
        "-created_at",
    )

    # --------------------------------------------------------
    # KPI VALUES
    # --------------------------------------------------------

    all_payments = list(
        SupplierPayment.objects.all()
    )

    posted_payments = [
        payment
        for payment in all_payments
        if payment.status
        == SupplierPayment.Status.POSTED
    ]

    total_paid = sum(
        (
            payment.amount
            for payment
            in posted_payments
        ),
        Decimal("0.00"),
    )

    current_month = (
        timezone.localdate().month
    )

    current_year = (
        timezone.localdate().year
    )

    month_paid = sum(
        (
            payment.amount
            for payment
            in posted_payments
            if (
                payment.payment_date.month
                == current_month
                and
                payment.payment_date.year
                == current_year
            )
        ),
        Decimal("0.00"),
    )

    voided_count = sum(
        1
        for payment in all_payments
        if payment.status
        == SupplierPayment.Status.VOIDED
    )

    context = {

        "payments":
            payments,

        "suppliers":
            Supplier.objects.order_by(
                "name"
            ),

        "search":
            search,

        "method":
            method,

        "status":
            status,

        "selected_supplier":
            supplier_id,

        "method_choices":
            SupplierPayment
            .PaymentMethod
            .choices,

        "status_choices":
            SupplierPayment
            .Status
            .choices,

        "total_records":
            len(all_payments),

        "posted_count":
            len(posted_payments),

        "voided_count":
            voided_count,

        "total_paid":
            total_paid,

        "month_paid":
            month_paid,

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        "payables/supplier_payment_list.html",
        context,
    )


# ============================================================
# RECORD SUPPLIER PAYMENT
# ============================================================

@login_required
def supplier_payment_create(request):

    currency_code = get_school_currency()

    selected_bill_id = (
        request.GET.get(
            "bill",
            ""
        )
        .strip()
    )

    available_bills = (
        SupplierBill.objects
        .filter(
            remaining_amount__gt=0,
        )
        .exclude(
            status=
                SupplierBill.Status.CANCELLED
        )
        .order_by(
            "-bill_date"
        )
    )

    if request.method == "POST":

        form = SupplierPaymentForm(
            request.POST,
            currency_code=currency_code,
        )

        if form.is_valid():

            try:

                payment = (
                    create_supplier_payment(
                        bill=
                            form.cleaned_data[
                                "bill"
                            ],

                        payment_date=
                            form.cleaned_data[
                                "payment_date"
                            ],

                        amount=
                            form.cleaned_data[
                                "amount"
                            ],

                        payment_method=
                            form.cleaned_data[
                                "payment_method"
                            ],

                        reference=
                            form.cleaned_data[
                                "reference"
                            ],

                        notes=
                            form.cleaned_data[
                                "notes"
                            ],
                    )
                )

            except ValidationError as error:

                message = (
                    error.messages[0]
                    if error.messages
                    else
                    "Unable to record this payment."
                )

                form.add_error(
                    None,
                    message,
                )

            else:

                messages.success(
                    request,
                    (
                        f"Supplier payment "
                        f"{payment.payment_number} "
                        f"was recorded successfully."
                    ),
                )

                return redirect(
                    "payables:supplier_payment_list"
                )

    else:

        initial = {
            "payment_date":
                timezone.localdate(),
        }

        if selected_bill_id:

            initial[
                "bill"
            ] = selected_bill_id

        form = SupplierPaymentForm(
            initial=initial,
            currency_code=currency_code,
        )

    # --------------------------------------------------------
    # Bill data used by the live frontend preview.
    # Strings are used intentionally so JSON serialization
    # stays simple and predictable.
    # --------------------------------------------------------

    bill_data = {}

    for bill in available_bills:

        bill_data[
            str(bill.pk)
        ] = {

            "bill_number":
                bill.bill_number,

            "supplier":
                bill.supplier.name,

            "supplier_id":
                str(
                    bill.supplier.pk
                ),

            "total_amount":
                str(
                    bill.total_amount
                ),

            "amount_paid":
                str(
                    bill.amount_paid
                ),

            "remaining_amount":
                str(
                    bill.remaining_amount
                ),

            "status":
                bill.status,

            "status_label":
                bill.get_status_display(),

            "bill_date":
                (
                    bill.bill_date.isoformat()
                    if bill.bill_date
                    else ""
                ),

            "due_date":
                (
                    bill.due_date.isoformat()
                    if bill.due_date
                    else ""
                ),
        }

    context = {

        "form":
            form,

        "page_title":
            "Record Supplier Payment",

        "submit_text":
            "Record Payment",

        "bill_data":
            bill_data,

        "currency_code":
            currency_code,
    }

    return render(
        request,
        "payables/supplier_payment_form.html",
        context,
    )

# ============================================================
# VOID SUPPLIER PAYMENT
# ============================================================

@login_required
@require_POST
def supplier_payment_void(
    request,
    pk,
):

    payment = get_object_or_404(
        SupplierPayment,
        pk=pk,
    )

    reason = (
        request.POST.get(
            "reason",
            ""
        )
        .strip()
    )

    try:

        void_supplier_payment(
            payment=payment,
            reason=reason,
        )

    except ValidationError as error:

        message = (
            error.messages[0]
            if error.messages
            else
            "Unable to void this payment."
        )

        messages.error(
            request,
            message,
        )

    else:

        messages.success(
            request,
            (
                f"Supplier payment "
                f"{payment.payment_number} "
                f"was voided successfully."
            ),
        )

    return redirect(
        "payables:supplier_payment_list"
    )




# ============================================================
# EXPENSE LIST
# ============================================================

@login_required
def expense_list(request):

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    category_id = (
        request.GET.get(
            "category",
            ""
        )
        .strip()
    )

    supplier_id = (
        request.GET.get(
            "supplier",
            ""
        )
        .strip()
    )

    payment_method = (
        request.GET.get(
            "payment_method",
            ""
        )
        .strip()
    )

    approval_status = (
        request.GET.get(
            "approval_status",
            ""
        )
        .strip()
    )

    record_status = (
        request.GET.get(
            "record_status",
            ""
        )
        .strip()
    )

    expenses = (
        Expense.objects.all()
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        matching_category_ids = list(
            ExpenseCategory.objects
            .filter(
                name__icontains=search
            )
            .values_list(
                "pk",
                flat=True,
            )
        )

        matching_supplier_ids = list(
            Supplier.objects
            .filter(
                name__icontains=search
            )
            .values_list(
                "pk",
                flat=True,
            )
        )

        expenses = expenses.filter(

            Q(
                expense_number__icontains=
                    search
            )
            |
            Q(
                description__icontains=
                    search
            )
            |
            Q(
                reference__icontains=
                    search
            )
            |
            Q(
                category_id__in=
                    matching_category_ids
            )
            |
            Q(
                supplier_id__in=
                    matching_supplier_ids
            )
        )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    if category_id:

        expenses = expenses.filter(
            category_id=category_id
        )

    if supplier_id:

        expenses = expenses.filter(
            supplier_id=supplier_id
        )

    if payment_method:

        expenses = expenses.filter(
            payment_method=
                payment_method
        )

    if approval_status:

        expenses = expenses.filter(
            approval_status=
                approval_status
        )

    if record_status:

        expenses = expenses.filter(
            record_status=
                record_status
        )

    expenses = expenses.order_by(
        "-expense_date",
        "-created_at",
    )

    # --------------------------------------------------------
    # KPI DATA
    # Use Python sums for predictable Mongo compatibility.
    # --------------------------------------------------------

    all_expenses = list(
        Expense.objects.all()
    )

    active_expenses = [
        expense
        for expense in all_expenses
        if (
            expense.record_status
            == Expense.RecordStatus.ACTIVE
        )
    ]

    total_expenses = sum(
        (
            expense.amount
            for expense
            in active_expenses
        ),
        Decimal("0.00"),
    )

    today = timezone.localdate()

    month_expenses = sum(
        (
            expense.amount
            for expense
            in active_expenses
            if (
                expense.expense_date.year
                == today.year
                and
                expense.expense_date.month
                == today.month
            )
        ),
        Decimal("0.00"),
    )

    pending_count = sum(
        1
        for expense in active_expenses
        if (
            expense.approval_status
            == Expense.ApprovalStatus.PENDING
        )
    )

    voided_count = sum(
        1
        for expense in all_expenses
        if (
            expense.record_status
            == Expense.RecordStatus.VOIDED
        )
    )

    context = {

        "expenses":
            expenses,

        "categories":
            ExpenseCategory.objects
            .order_by(
                "name"
            ),

        "suppliers":
            Supplier.objects
            .order_by(
                "name"
            ),

        "payment_method_choices":
            Expense
            .PaymentMethod
            .choices,

        "approval_status_choices":
            Expense
            .ApprovalStatus
            .choices,

        "record_status_choices":
            Expense
            .RecordStatus
            .choices,

        "search":
            search,

        "selected_category":
            category_id,

        "selected_supplier":
            supplier_id,

        "selected_payment_method":
            payment_method,

        "selected_approval_status":
            approval_status,

        "selected_record_status":
            record_status,

        "total_records":
            len(all_expenses),

        "active_count":
            len(active_expenses),

        "total_expenses":
            total_expenses,

        "month_expenses":
            month_expenses,

        "pending_count":
            pending_count,

        "voided_count":
            voided_count,

        "currency_code": 
            get_school_currency(),

    }

    return render(
        request,
        "payables/expense_list.html",
        context,
    )


# ============================================================
# CREATE EXPENSE
# ============================================================

@login_required
def expense_create(request):

    if request.method == "POST":

        form = ExpenseForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            expense = (
                form.save(
                    commit=False
                )
            )

            expense.created_by = (
                request.user
            )

            expense.save()

            messages.success(
                request,
                (
                    f"Expense "
                    f"{expense.expense_number} "
                    f"was recorded successfully."
                ),
            )

            return redirect(
                "payables:expense_detail",
                pk=expense.pk,
            )

    else:

        form = ExpenseForm(
            initial={
                "expense_date":
                    timezone.localdate(),
            }
        )

    context = {

        "form":
            form,

        "page_title":
            "Record Expense",

        "submit_text":
            "Record Expense",

        "is_edit":
            False,
    }

    return render(
     request,
    "payables/expense_form.html",
    {
        "form":
            form,

        "page_title":
            "Record Expense",

        "submit_text":
            "Record Expense",

        "is_edit":
            False,

        "currency_code":
            get_school_currency(),
    },
)


# ============================================================
# EDIT EXPENSE
# ============================================================

@login_required
def expense_edit(
    request,
    pk,
):

    expense = get_object_or_404(
        Expense,
        pk=pk,
    )

    if (
        expense.record_status
        == Expense.RecordStatus.VOIDED
    ):

        messages.error(
            request,
            (
                "Voided expenses cannot "
                "be edited."
            ),
        )

        return redirect(
            "payables:expense_detail",
            pk=expense.pk,
        )

    if request.method == "POST":

        form = ExpenseForm(
            request.POST,
            request.FILES,
            instance=expense,
        )

        if form.is_valid():

            expense = form.save()

            messages.success(
                request,
                (
                    f"Expense "
                    f"{expense.expense_number} "
                    f"was updated successfully."
                ),
            )

            return redirect(
                "payables:expense_detail",
                pk=expense.pk,
            )

    else:

        form = ExpenseForm(
            instance=expense
        )

    context = {

        "form":
            form,

        "expense":
            expense,

        "page_title":
            "Edit Expense",

        "submit_text":
            "Save Changes",

        "is_edit":
            True,
    }

    return render(
    request,
    "payables/expense_form.html",
    {
        "form":
            form,

        "expense":
            expense,

        "page_title":
            "Edit Expense",

        "submit_text":
            "Save Changes",

        "is_edit":
            True,

        "currency_code":
            get_school_currency(),
    },
)


# ============================================================
# EXPENSE DETAIL
# ============================================================

@login_required
def expense_detail(
    request,
    pk,
):

    expense = get_object_or_404(
        Expense,
        pk=pk,
    )

    context = {
        "expense":
            expense,
    }

    return render(
    request,
    "payables/expense_detail.html",
    {
        "expense":
            expense,

        "currency_code":
            get_school_currency(),
    },
)


# ============================================================
# VOID EXPENSE
# ============================================================

@login_required
@require_POST
def expense_void(
    request,
    pk,
):

    expense = get_object_or_404(
        Expense,
        pk=pk,
    )

    reason = (
        request.POST.get(
            "reason",
            ""
        )
        .strip()
    )

    try:

        void_expense(
            expense=expense,
            user=request.user,
            reason=reason,
        )

    except ValidationError as error:

        message = (
            error.messages[0]
            if error.messages
            else
            "Unable to void this expense."
        )

        messages.error(
            request,
            message,
        )

    else:

        messages.success(
            request,
            (
                f"Expense "
                f"{expense.expense_number} "
                f"was voided successfully."
            ),
        )

    return redirect(
        "payables:expense_detail",
        pk=expense.pk,
    )



# ============================================================
# EMPLOYEE FINANCIAL PROFILE LIST
# ============================================================

@login_required
def employee_financial_list(request):

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    status = (
        request.GET.get(
            "status",
            ""
        )
        .strip()
    )

    department = (
        request.GET.get(
            "department",
            ""
        )
        .strip()
    )

    employees = (
        EmployeeFinancialProfile
        .objects
        .all()
    )

    if search:

        employees = (
            employees.filter(
                Q(
                    employee_id__icontains=
                        search
                )
                |
                Q(
                    full_name__icontains=
                        search
                )
                |
                Q(
                    department__icontains=
                        search
                )
                |
                Q(
                    position__icontains=
                        search
                )
            )
        )

    if status:

        employees = (
            employees.filter(
                status=status
            )
        )

    if department:

        employees = (
            employees.filter(
                department=department
            )
        )

    employees = (
        employees.order_by(
            "full_name"
        )
    )

    all_employees = list(
        EmployeeFinancialProfile
        .objects
        .all()
    )

    active_count = sum(
        1
        for employee
        in all_employees
        if (
            employee.status
            ==
            EmployeeFinancialProfile
            .Status
            .ACTIVE
        )
    )

    all_transactions = list(
        EmployeeFinancialTransaction
        .objects
        .all()
    )

    posted_transactions = [
        transaction
        for transaction
        in all_transactions
        if (
            transaction.status
            ==
            EmployeeFinancialTransaction
            .Status
            .POSTED
        )
    ]

    total_activity = sum(
        (
            transaction.amount
            for transaction
            in posted_transactions
        ),
        Decimal("0.00"),
    )

    today = timezone.localdate()

    month_activity = sum(
        (
            transaction.amount
            for transaction
            in posted_transactions
            if (
                transaction.transaction_date.year
                == today.year
                and
                transaction.transaction_date.month
                == today.month
            )
        ),
        Decimal("0.00"),
    )

    departments = sorted(
        {
            employee.department
            for employee
            in all_employees
            if employee.department
        }
    )

    context = {

        "employees":
            employees,

        "search":
            search,

        "selected_status":
            status,

        "selected_department":
            department,

        "status_choices":
            EmployeeFinancialProfile
            .Status
            .choices,

        "departments":
            departments,

        "employee_count":
            len(all_employees),

        "active_count":
            active_count,

        "transaction_count":
            len(posted_transactions),

        "total_activity":
            total_activity,

        "month_activity":
            month_activity,

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        (
            "payables/"
            "employee_financial_list.html"
        ),
        context,
    )


# ============================================================
# CREATE EMPLOYEE FINANCIAL PROFILE
# ============================================================

@login_required
def employee_financial_create(request):

    if request.method == "POST":

        form = (
            EmployeeFinancialProfileForm(
                request.POST
            )
        )

        if form.is_valid():

            employee = form.save()

            messages.success(
                request,
                (
                    f"Employee financial profile "
                    f"{employee.employee_id} "
                    f"was created successfully."
                ),
            )

            return redirect(
                (
                    "payables:"
                    "employee_financial_detail"
                ),
                pk=employee.pk,
            )

    else:

        form = (
            EmployeeFinancialProfileForm()
        )

    return render(
        request,
        (
            "payables/"
            "employee_financial_form.html"
        ),
        {
            "form": form,
            "page_title":
                "Create Employee Financial Profile",
            "submit_text":
                "Create Profile",
            "is_edit":
                False,

            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# EDIT EMPLOYEE FINANCIAL PROFILE
# ============================================================

@login_required
def employee_financial_edit(
    request,
    pk,
):

    employee = get_object_or_404(
        EmployeeFinancialProfile,
        pk=pk,
    )

    if request.method == "POST":

        form = (
            EmployeeFinancialProfileForm(
                request.POST,
                instance=employee,
            )
        )

        if form.is_valid():

            employee = form.save()

            messages.success(
                request,
                (
                    f"Employee financial profile "
                    f"{employee.employee_id} "
                    f"was updated successfully."
                ),
            )

            return redirect(
                (
                    "payables:"
                    "employee_financial_detail"
                ),
                pk=employee.pk,
            )

    else:

        form = (
            EmployeeFinancialProfileForm(
                instance=employee
            )
        )

    return render(
        request,
        (
            "payables/"
            "employee_financial_form.html"
        ),
        {
            "form":
                form,

            "employee":
                employee,

            "page_title":
                "Edit Employee Financial Profile",

            "submit_text":
                "Save Changes",

            "is_edit":
                True,

            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# EMPLOYEE FINANCIAL DETAIL
# ============================================================

@login_required
def employee_financial_detail(
    request,
    pk,
):

    employee = get_object_or_404(
        EmployeeFinancialProfile,
        pk=pk,
    )

    transactions = list(
        employee
        .financial_transactions
        .all()
        .order_by(
            "-transaction_date",
            "-created_at",
        )
    )

    posted = [
        transaction
        for transaction
        in transactions
        if (
            transaction.status
            ==
            EmployeeFinancialTransaction
            .Status
            .POSTED
        )
    ]

    def total_for(
        transaction_type
    ):

        return sum(
            (
                transaction.amount
                for transaction
                in posted
                if (
                    transaction.transaction_type
                    ==
                    transaction_type
                )
            ),
            Decimal("0.00"),
        )

    context = {

        "employee":
            employee,

        "transactions":
            transactions,

        "advance_total":
            total_for(
                EmployeeFinancialTransaction
                .TransactionType
                .ADVANCE
            ),

        "reimbursement_total":
            total_for(
                EmployeeFinancialTransaction
                .TransactionType
                .REIMBURSEMENT
            ),

        "allowance_total":
            total_for(
                EmployeeFinancialTransaction
                .TransactionType
                .ALLOWANCE
            ),

        "deduction_total":
            total_for(
                EmployeeFinancialTransaction
                .TransactionType
                .DEDUCTION
            ),

        "payment_total":
            total_for(
                EmployeeFinancialTransaction
                .TransactionType
                .PAYMENT
            ),

        "posted_transaction_count":
            len(posted),

        "currency_code":
            get_school_currency(),
    }

    return render(
        request,
        (
            "payables/"
            "employee_financial_detail.html"
        ),
        context,
    )


# ============================================================
# CREATE EMPLOYEE FINANCIAL TRANSACTION
# ============================================================

@login_required
def employee_financial_transaction_create(
    request,
):

    employee_id = (
        request.GET.get(
            "employee",
            ""
        )
        .strip()
    )

    available_employees = (
        EmployeeFinancialProfile
        .objects
        .filter(
            status=
                EmployeeFinancialProfile
                .Status
                .ACTIVE
        )
        .order_by(
            "full_name"
        )
    )

    if request.method == "POST":

        form = (
            EmployeeFinancialTransactionForm(
                request.POST
            )
        )

        if form.is_valid():

            transaction = (
                form.save(
                    commit=False
                )
            )

            transaction.created_by = (
                request.user
            )

            transaction.save()

            messages.success(
                request,
                (
                    f"Financial transaction "
                    f"{transaction.transaction_number} "
                    f"was recorded successfully."
                ),
            )

            return redirect(
                (
                    "payables:"
                    "employee_financial_detail"
                ),
                pk=
                    transaction.employee.pk,
            )

    else:

        initial = {
            "transaction_date":
                timezone.localdate(),
        }

        if employee_id:

            initial[
                "employee"
            ] = employee_id

        form = (
            EmployeeFinancialTransactionForm(
                initial=initial
            )
        )

    employee_data = {}

    for employee in available_employees:

        posted_transactions = list(
            employee
            .financial_transactions
            .filter(
                status=
                    EmployeeFinancialTransaction
                    .Status
                    .POSTED
            )
        )

        advance_total = sum(
            (
                transaction.amount
                for transaction
                in posted_transactions
                if (
                    transaction.transaction_type
                    ==
                    EmployeeFinancialTransaction
                    .TransactionType
                    .ADVANCE
                )
            ),
            Decimal("0.00"),
        )

        deduction_total = sum(
            (
                transaction.amount
                for transaction
                in posted_transactions
                if (
                    transaction.transaction_type
                    ==
                    EmployeeFinancialTransaction
                    .TransactionType
                    .DEDUCTION
                )
            ),
            Decimal("0.00"),
        )

        employee_data[
            str(employee.pk)
        ] = {

            "employee_id":
                employee.employee_id,

            "name":
                employee.full_name,

            "department":
                employee.department,

            "position":
                employee.position,

            "salary":
                (
                    str(
                        employee
                        .base_salary_reference
                    )
                    if (
                        employee
                        .base_salary_reference
                        is not None
                    )
                    else "0"
                ),

            "advance_total":
                str(advance_total),

            "deduction_total":
                str(deduction_total),

            "transaction_count":
                len(
                    posted_transactions
                ),
        }

    return render(
        request,
        (
            "payables/"
            "employee_financial_transaction_form.html"
        ),
        {
            "form":
                form,

            "page_title":
                (
                    "Record Employee "
                    "Financial Transaction"
                ),

            "submit_text":
                "Record Transaction",

            "employee_data":
                employee_data,

            "currency_code":
                get_school_currency(),
        },
    )

    employee_id = (
        request.GET.get(
            "employee",
            ""
        )
        .strip()
    )

    if request.method == "POST":

        form = (
            EmployeeFinancialTransactionForm(
                request.POST
            )
        )

        if form.is_valid():

            transaction = (
                form.save(
                    commit=False
                )
            )

            transaction.created_by = (
                request.user
            )

            transaction.save()

            messages.success(
                request,
                (
                    f"Financial transaction "
                    f"{transaction.transaction_number} "
                    f"was recorded successfully."
                ),
            )

            return redirect(
                (
                    "payables:"
                    "employee_financial_detail"
                ),
                pk=
                    transaction.employee.pk,
            )

    else:

        initial = {
            "transaction_date":
                timezone.localdate(),
        }

        if employee_id:

            initial[
                "employee"
            ] = employee_id

        form = (
            EmployeeFinancialTransactionForm(
                initial=initial
            )
        )

    return render(
        request,
        (
            "payables/"
            "employee_financial_transaction_form.html"
        ),
        {
            "form":
                form,

            "page_title":
                "Record Employee Financial Transaction",

            "submit_text":
                "Record Transaction",
        },
    )


# ============================================================
# VOID EMPLOYEE FINANCIAL TRANSACTION
# ============================================================

@login_required
@require_POST
def employee_financial_transaction_void(
    request,
    pk,
):

    transaction = get_object_or_404(
        EmployeeFinancialTransaction,
        pk=pk,
    )

    employee_pk = (
        transaction.employee.pk
    )

    reason = (
        request.POST.get(
            "reason",
            ""
        )
        .strip()
    )

    try:

        void_employee_financial_transaction(
            transaction=transaction,
            user=request.user,
            reason=reason,
        )

    except ValidationError as error:

        message = (
            error.messages[0]
            if error.messages
            else
            (
                "Unable to void this "
                "financial transaction."
            )
        )

        messages.error(
            request,
            message,
        )

    else:

        messages.success(
            request,
            (
                f"Transaction "
                f"{transaction.transaction_number} "
                f"was voided successfully."
            ),
        )

    return redirect(
        (
            "payables:"
            "employee_financial_detail"
        ),
        pk=employee_pk,
    )


# ============================================================
# APPROVAL WORKFLOW
# ============================================================


def _approval_validation_message(
    error,
):

    if (
        hasattr(
            error,
            "messages",
        )
        and
        error.messages
    ):

        return " ".join(
            error.messages
        )

    return str(
        error
    )


@login_required
def approval_list(
    request,
):

    approvals = (
        ApprovalRequest.objects
        .all()
        .order_by(
            "-created_at"
        )
    )

    search = (
        request.GET
        .get(
            "search",
            "",
        )
        .strip()
    )

    selected_status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    selected_operation = (
        request.GET
        .get(
            "operation_type",
            "",
        )
        .strip()
    )

    selected_requester = (
        request.GET
        .get(
            "requester",
            "",
        )
        .strip()
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        approvals = (
            approvals.filter(

                Q(
                    request_number__icontains=
                    search
                )

                |

                Q(
                    title__icontains=
                    search
                )

                |

                Q(
                    description__icontains=
                    search
                )

                |

                Q(
                    request_reason__icontains=
                    search
                )

                |

                Q(
                    related_entity_type__icontains=
                    search
                )

                |

                Q(
                    related_entity_id__icontains=
                    search
                )
            )
        )


    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if selected_status:

        approvals = (
            approvals.filter(
                status=
                    selected_status
            )
        )


    # --------------------------------------------------------
    # OPERATION FILTER
    # --------------------------------------------------------

    if selected_operation:

        approvals = (
            approvals.filter(
                operation_type=
                    selected_operation
            )
        )


    # --------------------------------------------------------
    # REQUESTER FILTER
    # --------------------------------------------------------

    if selected_requester:

        approvals = (
            approvals.filter(
                requester_id=
                    selected_requester
            )
        )


    # --------------------------------------------------------
    # GLOBAL KPI COUNTS
    # --------------------------------------------------------

    all_approvals = (
        ApprovalRequest.objects
        .all()
    )


    total_count = (
        all_approvals.count()
    )


    requested_count = (
        all_approvals.filter(
            status=
                ApprovalRequest
                .Status
                .REQUESTED
        )
        .count()
    )


    pending_count = (
        all_approvals.filter(
            status=
                ApprovalRequest
                .Status
                .PENDING
        )
        .count()
    )


    approved_count = (
        all_approvals.filter(
            status=
                ApprovalRequest
                .Status
                .APPROVED
        )
        .count()
    )


    rejected_count = (
        all_approvals.filter(
            status=
                ApprovalRequest
                .Status
                .REJECTED
        )
        .count()
    )


    processed_count = (
        all_approvals.filter(
            status=
                ApprovalRequest
                .Status
                .PROCESSED
        )
        .count()
    )


    User = (
        get_user_model()
    )


    requesters = (
        User.objects
        .filter(
            requested_approvals__isnull=False
        )
        .distinct()
        .order_by(
            "username"
        )
    )


    context = {

        "approvals":
            approvals,

        "search":
            search,

        "selected_status":
            selected_status,

        "selected_operation":
            selected_operation,

        "selected_requester":
            selected_requester,

        "status_choices":
            ApprovalRequest
            .Status
            .choices,

        "operation_choices":
            ApprovalRequest
            .OperationType
            .choices,

        "requesters":
            requesters,

        "total_count":
            total_count,

        "requested_count":
            requested_count,

        "pending_count":
            pending_count,

        "approved_count":
            approved_count,

        "rejected_count":
            rejected_count,

        "processed_count":
            processed_count,

        "currency_code":
            get_school_currency(),
    }


    return render(
        request,
        (
            "payables/"
            "approval_list.html"
        ),
        context,
    )


@login_required
def approval_create(
    request,
):

    if request.method == "POST":

        form = (
            ApprovalRequestForm(
                request.POST
            )
        )


        if form.is_valid():

            approval = (
                form.save(
                    commit=False
                )
            )


            approval.requester = (
                request.user
            )


            approval.status = (
                ApprovalRequest
                .Status
                .REQUESTED
            )


            approval.full_clean()

            approval.save()


            messages.success(
                request,
                (
                    "Approval request "
                    f"{approval.request_number} "
                    "was created successfully."
                ),
            )


            return redirect(
                "payables:approval_detail",
                pk=approval.pk,
            )


    else:

        form = (
            ApprovalRequestForm()
        )


    return render(
        request,
        (
            "payables/"
            "approval_form.html"
        ),
        {
            "form":
                form,

            "page_title":
                "Create Approval Request",

            "submit_text":
                "Create Request",

            "is_edit":
                False,

            "currency_code":
                get_school_currency(),
        },
    )


@login_required
def approval_edit(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    if (
        approval.status
        !=
        ApprovalRequest
        .Status
        .REQUESTED
    ):

        messages.error(
            request,
            (
                "Only approval requests "
                "in Requested status "
                "can be edited."
            ),
        )

        return redirect(
            "payables:approval_detail",
            pk=approval.pk,
        )


    if request.method == "POST":

        form = (
            ApprovalRequestForm(
                request.POST,
                instance=approval,
            )
        )


        if form.is_valid():

            approval = (
                form.save(
                    commit=False
                )
            )

            approval.full_clean()

            approval.save()


            messages.success(
                request,
                (
                    "Approval request "
                    "was updated successfully."
                ),
            )


            return redirect(
                "payables:approval_detail",
                pk=approval.pk,
            )


    else:

        form = (
            ApprovalRequestForm(
                instance=approval
            )
        )


    return render(
        request,
        (
            "payables/"
            "approval_form.html"
        ),
        {
            "form":
                form,

            "approval":
                approval,

            "page_title":
                "Edit Approval Request",

            "submit_text":
                "Save Changes",

            "is_edit":
                True,

            "currency_code":
                get_school_currency(),
        },
    )


@login_required
def approval_detail(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    return render(
        request,
        (
            "payables/"
            "approval_detail.html"
        ),
        {
            "approval":
                approval,

            "currency_code":
                get_school_currency(),
        },
    )


@login_required
@require_POST
def approval_submit(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    try:

        approval = (
            submit_approval_request(
                approval
            )
        )


        messages.success(
            request,
            (
                f"{approval.request_number} "
                "was submitted for approval."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            _approval_validation_message(
                error
            ),
        )


    return redirect(
        "payables:approval_detail",
        pk=approval.pk,
    )


@login_required
@require_POST
def approval_approve(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    comments = (
        request.POST
        .get(
            "comments",
            "",
        )
    )


    try:

         if (
            approval.operation_type
            ==
            ApprovalRequest
            .OperationType
            .DISCOUNT
            and
            (
                approval.related_entity_type
                or ""
            ).strip().lower()
            ==
            "discount"
         ):

            discount = (
                approve_discount_approval(
                    approval_request=approval,
                    approver=request.user,
                    comments=comments,
                )
            )

            approval = (
                discount.approval_request
            )

         else:

            approval = (
                approve_approval_request(
                    approval,
                    request.user,
                    comments,
                )
            )


         messages.success(
            request,
            (
                f"{approval.request_number} "
                "was approved."
            ),
         )


    except ValidationError as error:

         messages.error(
            request,
            _approval_validation_message(
                error
            ),
        )


    return redirect(
        "payables:approval_detail",
        pk=approval.pk,
    )


@login_required
@require_POST
def approval_reject(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    comments = (
        request.POST
        .get(
            "comments",
            "",
        )
    )


    try:

        if (
            approval.operation_type
            ==
            ApprovalRequest
            .OperationType
            .DISCOUNT
            and
            (
                approval.related_entity_type
                or ""
            ).strip().lower()
            ==
            "discount"
        ):

            discount = (
                reject_discount_approval(
                    approval_request=approval,
                    approver=request.user,
                    comments=comments,
                )
            )

            approval = (
                discount.approval_request
            )

        else:

            approval = (
                reject_approval_request(
                    approval,
                    request.user,
                    comments,
                )
            )


        messages.success(
            request,
            (
                f"{approval.request_number} "
                "was rejected."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            _approval_validation_message(
                error
            ),
        )


    return redirect(
        "payables:approval_detail",
        pk=approval.pk,
    )


@login_required
@require_POST
def approval_process(
    request,
    pk,
):

    approval = (
        get_object_or_404(
            ApprovalRequest,
            pk=pk,
        )
    )


    try:

        approval = (
            process_approval_request(
                approval,
                request.user,
            )
        )


        messages.success(
            request,
            (
                f"{approval.request_number} "
                "was marked as processed."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            _approval_validation_message(
                error
            ),
        )


    return redirect(
        "payables:approval_detail",
        pk=approval.pk,
    )






# ============================================================
# DISCOUNTS
# ============================================================

@login_required
def discount_list(request):

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

    discount_type = (
        request.GET
        .get(
            "discount_type",
            "",
        )
        .strip()
    )

    value_type = (
        request.GET
        .get(
            "value_type",
            "",
        )
        .strip()
    )

    approval = (
        request.GET
        .get(
            "approval",
            "",
        )
        .strip()
    )

    discounts = (
        Discount.objects
        .all()
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        discounts = (
            discounts.filter(
                Q(
                    discount_number__icontains=
                        search
                )
                |
                Q(
                    student_reference__icontains=
                        search
                )
                |
                Q(
                    invoice_reference__icontains=
                        search
                )
                |
                Q(
                    reason__icontains=
                        search
                )
            )
        )


    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    valid_statuses = {
        choice[0]
        for choice
        in Discount.Status.choices
    }

    if status in valid_statuses:

        discounts = (
            discounts.filter(
                status=status
            )
        )


    # --------------------------------------------------------
    # DISCOUNT TYPE FILTER
    # --------------------------------------------------------

    valid_discount_types = {
        choice[0]
        for choice
        in Discount.DiscountType.choices
    }

    if discount_type in valid_discount_types:

        discounts = (
            discounts.filter(
                discount_type=
                    discount_type
            )
        )


    # --------------------------------------------------------
    # VALUE TYPE FILTER
    # --------------------------------------------------------

    valid_value_types = {
        choice[0]
        for choice
        in Discount.ValueType.choices
    }

    if value_type in valid_value_types:

        discounts = (
            discounts.filter(
                value_type=
                    value_type
            )
        )


    # --------------------------------------------------------
    # APPROVAL FILTER
    # --------------------------------------------------------

    if approval == "required":

        discounts = (
            discounts.filter(
                requires_approval=True
            )
        )

    elif approval == "not_required":

        discounts = (
            discounts.filter(
                requires_approval=False
            )
        )


    # --------------------------------------------------------
    # KPI DATA
    # --------------------------------------------------------

    all_discounts = (
        Discount.objects.all()
    )

    total_discounts = (
        all_discounts.count()
    )

    draft_count = (
        all_discounts.filter(
            status=
                Discount.Status.DRAFT
        )
        .count()
    )

    pending_count = (
        all_discounts.filter(
            status=
                Discount.Status
                .PENDING_APPROVAL
        )
        .count()
    )

    approved_count = (
        all_discounts.filter(
            status=
                Discount.Status.APPROVED
        )
        .count()
    )

    applied_count = (
        all_discounts.filter(
            status=
                Discount.Status.APPLIED
        )
        .count()
    )

    fixed_amount_total = (
        Decimal("0.00")
    )

    for item in (
        all_discounts.filter(
            value_type=
                Discount.ValueType
                .FIXED_AMOUNT
        )
        .exclude(
            status=
                Discount.Status.CANCELLED
        )
    ):

        fixed_amount_total += (
            item.value
            or Decimal("0.00")
        )


    context = {

        "discounts":
            discounts,

        "search":
            search,

        "status":
            status,

        "selected_discount_type":
            discount_type,

        "selected_value_type":
            value_type,

        "selected_approval":
            approval,

        "status_choices":
            Discount.Status.choices,

        "discount_type_choices":
            Discount.DiscountType.choices,

        "value_type_choices":
            Discount.ValueType.choices,

        "total_discounts":
            total_discounts,

        "draft_count":
            draft_count,

        "pending_count":
            pending_count,

        "approved_count":
            approved_count,

        "applied_count":
            applied_count,

        "fixed_amount_total":
            fixed_amount_total,

        "currency_code":
            get_school_currency(),
    }


    return render(
        request,
        (
            "payables/"
            "discount_list.html"
        ),
        context,
    )


# ============================================================
# CREATE DISCOUNT
# ============================================================

@login_required
def discount_create(request):

    if request.method == "POST":

        form = DiscountForm(
            request.POST
        )

        if form.is_valid():

            try:

                discount = (
                    create_discount(
                        user=request.user,

                        student_reference=
                            form.cleaned_data[
                                "student_reference"
                            ],

                        invoice_reference=
                            form.cleaned_data[
                                "invoice_reference"
                            ],

                        discount_type=
                            form.cleaned_data[
                                "discount_type"
                            ],

                        value_type=
                            form.cleaned_data[
                                "value_type"
                            ],

                        value=
                            form.cleaned_data[
                                "value"
                            ],

                        reason=
                            form.cleaned_data[
                                "reason"
                            ],

                        discount_date=
                            form.cleaned_data[
                                "discount_date"
                            ],

                        requires_approval=
                            form.cleaned_data[
                                "requires_approval"
                            ],
                    )
                )

                messages.success(
                    request,
                    (
                        f"{discount.discount_number} "
                        "was created successfully."
                    ),
                )

                return redirect(
                    "payables:discount_detail",
                    pk=discount.pk,
                )

            except ValidationError as error:

                _add_validation_error_to_form(
                    form,
                    error,
                )

    else:

        form = DiscountForm(
            initial={
                "discount_date":
                    timezone.localdate(),
            }
        )


    return render(
        request,
        (
            "payables/"
            "discount_form.html"
        ),
        {
            "form":
                form,

            "page_title":
                "Create Discount",

            "submit_text":
                "Create Discount",

            "is_edit":
                False,

            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# EDIT DISCOUNT
# ============================================================

@login_required
def discount_edit(
    request,
    pk,
):

    discount = (
        get_object_or_404(
            Discount,
            pk=pk,
        )
    )


    if (
        discount.status
        != Discount.Status.DRAFT
    ):

        messages.error(
            request,
            (
                "Only draft discounts "
                "can be edited."
            ),
        )

        return redirect(
            "payables:discount_detail",
            pk=discount.pk,
        )


    if request.method == "POST":

        form = DiscountForm(
            request.POST,
            instance=discount,
        )

        if form.is_valid():

            try:

                discount = (
                    update_discount(
                        discount=discount,

                        student_reference=
                            form.cleaned_data[
                                "student_reference"
                            ],

                        invoice_reference=
                            form.cleaned_data[
                                "invoice_reference"
                            ],

                        discount_type=
                            form.cleaned_data[
                                "discount_type"
                            ],

                        value_type=
                            form.cleaned_data[
                                "value_type"
                            ],

                        value=
                            form.cleaned_data[
                                "value"
                            ],

                        reason=
                            form.cleaned_data[
                                "reason"
                            ],

                        discount_date=
                            form.cleaned_data[
                                "discount_date"
                            ],

                        requires_approval=
                            form.cleaned_data[
                                "requires_approval"
                            ],
                    )
                )

                messages.success(
                    request,
                    (
                        f"{discount.discount_number} "
                        "was updated successfully."
                    ),
                )

                return redirect(
                    "payables:discount_detail",
                    pk=discount.pk,
                )

            except ValidationError as error:

                _add_validation_error_to_form(
                    form,
                    error,
                )

    else:

        form = DiscountForm(
            instance=discount
        )


    return render(
        request,
        (
            "payables/"
            "discount_form.html"
        ),
        {
            "form":
                form,

            "discount":
                discount,

            "page_title":
                "Edit Discount",

            "submit_text":
                "Save Changes",

            "is_edit":
                True,

            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# DISCOUNT DETAIL
# ============================================================

@login_required
def discount_detail(
    request,
    pk,
):

    discount = (
        get_object_or_404(
            Discount,
            pk=pk,
        )
    )

    approval_request = (
        discount.approval_request
        if discount.approval_request_id
        else None
    )


    return render(
        request,
        (
            "payables/"
            "discount_detail.html"
        ),
        {
            "discount":
                discount,

            "approval_request":
                approval_request,

            "currency_code":
                get_school_currency(),
        },
    )


# ============================================================
# SUBMIT DISCOUNT
# ============================================================

@login_required
@require_POST
def discount_submit(
    request,
    pk,
):

    discount = (
        get_object_or_404(
            Discount,
            pk=pk,
        )
    )


    try:

        discount = (
            submit_discount(
                discount=discount
            )
        )

        if (
            discount.status
            ==
            Discount.Status
            .PENDING_APPROVAL
        ):

            messages.success(
                request,
                (
                    f"{discount.discount_number} "
                    "was submitted for approval."
                ),
            )

        else:

            messages.success(
                request,
                (
                    f"{discount.discount_number} "
                    "was approved because no "
                    "separate approval was required."
                ),
            )


    except ValidationError as error:

        messages.error(
            request,
            (
                error.messages[0]
                if error.messages
                else
                "Unable to submit discount."
            ),
        )


    return redirect(
        "payables:discount_detail",
        pk=discount.pk,
    )


# ============================================================
# CANCEL DISCOUNT
# ============================================================

@login_required
@require_POST
def discount_cancel(
    request,
    pk,
):

    discount = (
        get_object_or_404(
            Discount,
            pk=pk,
        )
    )

    reason = (
        request.POST
        .get(
            "reason",
            "",
        )
    )


    try:

        discount = (
            cancel_discount(
                discount=discount,
                user=request.user,
                reason=reason,
            )
        )

        messages.success(
            request,
            (
                f"{discount.discount_number} "
                "was cancelled."
            ),
        )


    except ValidationError as error:

        messages.error(
            request,
            (
                error.messages[0]
                if error.messages
                else
                "Unable to cancel discount."
            ),
        )


    return redirect(
        "payables:discount_detail",
        pk=discount.pk,
    )
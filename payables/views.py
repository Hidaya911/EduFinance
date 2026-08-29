from datetime import timedelta
from decimal import Decimal


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
)

from .models import (
    ExpenseCategory,
    Supplier,
    SupplierBill,
    SupplierPayment,
    Expense,
)

from .services import (
    create_supplier_payment,
    void_supplier_payment,
    void_expense,
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

            bill = form.save()

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

            bill = form.save()

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
            request.POST
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
            initial=initial
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
        context,
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
        context,
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
        context,
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
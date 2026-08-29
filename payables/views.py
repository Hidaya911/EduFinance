from datetime import timedelta
from decimal import Decimal

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
)

from .models import (
    ExpenseCategory,
    Supplier,
    SupplierBill,
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
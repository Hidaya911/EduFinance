from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .forms import (
    ExpenseCategoryForm,
    SupplierForm,
)

from .models import (
    ExpenseCategory,
    Supplier,
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
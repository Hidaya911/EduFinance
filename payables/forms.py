import os

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    ExpenseCategory,
    Supplier,
    SupplierBill,
    SupplierPayment,
    Expense,
    EmployeeFinancialProfile,
    EmployeeFinancialTransaction,
    ApprovalRequest,
)


class ExpenseCategoryForm(forms.ModelForm):

    class Meta:
        model = ExpenseCategory

        fields = [
            "name",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Maintenance",
                    "autocomplete": "off",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional description...",
                    "rows": 4,
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        existing = ExpenseCategory.objects.filter(
            name__iexact=name
        )

        if self.instance.pk:
            existing = existing.exclude(
                pk=self.instance.pk
            )

        if existing.exists():
            raise forms.ValidationError(
                "An expense category with this name "
                "already exists."
            )

        return name


class SupplierForm(forms.ModelForm):

    class Meta:
        model = Supplier

        fields = [
            "name",
            "contact_person",
            "phone",
            "email",
            "address",
            "tax_number",
            "notes",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Cedar Stationery SAL",
                    "autocomplete": "off",
                }
            ),

            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact person name",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+961 ...",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "supplier@example.com",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Supplier address",
                    "rows": 3,
                }
            ),

            "tax_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tax / registration number",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional notes...",
                    "rows": 4,
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        existing = Supplier.objects.filter(
            name__iexact=name
        )

        if self.instance.pk:
            existing = existing.exclude(
                pk=self.instance.pk
            )

        if existing.exists():
            raise forms.ValidationError(
                "A supplier with this name already exists."
            )

        return name


class SupplierBillForm(forms.ModelForm):

    class Meta:
        model = SupplierBill

        fields = [
            "bill_number",
            "supplier",
            "bill_date",
            "due_date",
            "description",
            "total_amount",
            "document",
        ]

        widgets = {

            "bill_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "e.g. BILL-2026-001",
                    "autocomplete": "off",
                }
            ),

            "supplier": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "bill_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder":
                        "Describe the products, services, invoice items or purpose of this bill...",
                }
            ),

            "total_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept":
                        ".pdf,.png,.jpg,.jpeg",
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "supplier"
        ].queryset = Supplier.objects.order_by(
            "name"
        )

        self.fields[
            "supplier"
        ].empty_label = "Select supplier"

    def clean_bill_number(self):

        bill_number = (
            self.cleaned_data[
                "bill_number"
            ]
            .strip()
        )

        existing = SupplierBill.objects.filter(
            bill_number__iexact=bill_number
        )

        if self.instance.pk:
            existing = existing.exclude(
                pk=self.instance.pk
            )

        if existing.exists():
            raise forms.ValidationError(
                "A supplier bill with this bill number already exists."
            )

        return bill_number

    def clean_supplier(self):

        supplier = self.cleaned_data[
            "supplier"
        ]

        # Allow an existing bill to keep its current supplier,
        # even if that supplier was later deactivated.
        if (
            self.instance.pk
            and self.instance.supplier_id
            == supplier.pk
        ):
            return supplier

        if not supplier.is_active:
            raise forms.ValidationError(
                "Inactive suppliers cannot be assigned to new bills."
            )

        return supplier

    def clean_total_amount(self):

        total_amount = self.cleaned_data[
            "total_amount"
        ]

        if total_amount <= 0:
            raise forms.ValidationError(
                "Bill total must be greater than zero."
            )

        if (
            self.instance.pk
            and self.instance.amount_paid
            and total_amount
            < self.instance.amount_paid
        ):
            raise forms.ValidationError(
                "Bill total cannot be lower than the amount already paid."
            )

        return total_amount

    def clean_document(self):

        document = self.cleaned_data.get(
            "document"
        )

        if not document:
            return document

        # Existing stored file.
        if not hasattr(
            document,
            "size",
        ):
            return document

        max_size = (
            5 * 1024 * 1024
        )

        if document.size > max_size:
            raise forms.ValidationError(
                "Document size cannot exceed 5 MB."
            )

        extension = (
            os.path.splitext(
                document.name
            )[1]
            .lower()
        )

        allowed_extensions = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
        }

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Only PDF, PNG, JPG and JPEG files are allowed."
            )

        return document

    def clean(self):

        cleaned_data = super().clean()

        bill_date = cleaned_data.get(
            "bill_date"
        )

        due_date = cleaned_data.get(
            "due_date"
        )

        if (
            bill_date
            and due_date
            and due_date < bill_date
        ):

            self.add_error(
                "due_date",
                "Due date cannot be earlier than the bill date.",
            )

        return cleaned_data

    





# ============================================================
# SUPPLIER PAYMENT FORM
# ============================================================

class SupplierPaymentForm(forms.ModelForm):

    class Meta:

        model = SupplierPayment

        fields = [
            "bill",
            "payment_date",
            "amount",
            "payment_method",
            "reference",
            "notes",
        ]

        widgets = {

            "bill": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "payment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        (
                            "Bank reference, cheque number "
                            "or transaction reference"
                        ),
                    "autocomplete": "off",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder":
                        (
                            "Optional notes about "
                            "this supplier payment..."
                        ),
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "bill"
        ].queryset = (
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

        self.fields[
            "bill"
        ].empty_label = (
            "Select unpaid supplier bill"
        )
        self.fields[
          "bill"
            ].label_from_instance = (
                lambda bill:
                (
                    f"{bill.bill_number} — "
                    f"{bill.supplier.name} — "
                    f"${bill.remaining_amount:.2f} remaining"
                )
             )
    def clean_amount(self):

        amount = self.cleaned_data[
            "amount"
        ]

        if amount <= 0:

            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )

        return amount

    def clean(self):

        cleaned_data = (
            super().clean()
        )

        bill = cleaned_data.get(
            "bill"
        )

        amount = cleaned_data.get(
            "amount"
        )

        if not bill or amount is None:
            return cleaned_data

        if (
            bill.status
            == SupplierBill.Status.CANCELLED
        ):

            self.add_error(
                "bill",
                (
                    "Payments cannot be recorded "
                    "against a cancelled bill."
                ),
            )

            return cleaned_data

        if (
            bill.remaining_amount
            <= 0
        ):

            self.add_error(
                "bill",
                "This supplier bill is already fully paid.",
            )

            return cleaned_data

        if (
            amount
            > bill.remaining_amount
        ):

            self.add_error(
                "amount",
                (
                    "Payment amount cannot be greater "
                    "than the remaining bill balance "
                    f"of ${bill.remaining_amount:.2f}."
                ),
            )

        return cleaned_data



    # ============================================================
# EXPENSE FORM
# ============================================================

class ExpenseForm(forms.ModelForm):

    class Meta:

        model = Expense

        fields = [
            "category",
            "supplier",
            "description",
            "amount",
            "expense_date",
            "payment_method",
            "reference",
            "receipt",
            "approval_status",
        ]

        widgets = {

            "category": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "supplier": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder":
                        (
                            "Describe the school expense, "
                            "purpose, goods or services..."
                        ),
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),

            "expense_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        (
                            "Transaction reference, "
                            "cheque number or receipt ID"
                        ),
                    "autocomplete": "off",
                }
            ),

            "receipt": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept":
                        ".pdf,.png,.jpg,.jpeg",
                }
            ),

            "approval_status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        # --------------------------------------------------------
        # CATEGORY QUERYSET
        # --------------------------------------------------------

        active_categories = (
            ExpenseCategory.objects
            .filter(
                is_active=True
            )
            .order_by(
                "name"
            )
        )

        # Preserve an existing inactive category
        # while editing historical financial data.
        if (
            self.instance
            and
            self.instance.pk
            and
            self.instance.category_id
        ):

            current_category = (
                ExpenseCategory.objects
                .filter(
                    pk=
                        self.instance.category_id
                )
            )

            self.fields[
                "category"
            ].queryset = (
                active_categories
                |
                current_category
            )

        else:

            self.fields[
                "category"
            ].queryset = (
                active_categories
            )

        # --------------------------------------------------------
        # SUPPLIER QUERYSET
        # --------------------------------------------------------

        active_suppliers = (
            Supplier.objects
            .filter(
                is_active=True
            )
            .order_by(
                "name"
            )
        )

        if (
            self.instance
            and
            self.instance.pk
            and
            self.instance.supplier_id
        ):

            current_supplier = (
                Supplier.objects
                .filter(
                    pk=
                        self.instance.supplier_id
                )
            )

            self.fields[
                "supplier"
            ].queryset = (
                active_suppliers
                |
                current_supplier
            )

        else:

            self.fields[
                "supplier"
            ].queryset = (
                active_suppliers
            )

        self.fields[
            "supplier"
        ].required = False

        self.fields[
            "supplier"
        ].empty_label = (
            "No supplier / direct expense"
        )

    def clean_amount(self):

        amount = self.cleaned_data[
            "amount"
        ]

        if amount <= 0:

            raise forms.ValidationError(
                "Expense amount must be greater than zero."
            )

        return amount

    def clean_receipt(self):

        receipt = self.cleaned_data.get(
            "receipt"
        )

        if not receipt:

            return receipt

        # Existing stored FileField values may not
        # expose uploaded-file size in the same way.
        if hasattr(
            receipt,
            "size",
        ):

            max_size = (
                5
                *
                1024
                *
                1024
            )

            if receipt.size > max_size:

                raise forms.ValidationError(
                    "Receipt file cannot exceed 5 MB."
                )

        filename = (
            getattr(
                receipt,
                "name",
                "",
            )
            .lower()
        )

        allowed_extensions = (
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
        )

        if (
            filename
            and
            not filename.endswith(
                allowed_extensions
            )
        ):

            raise forms.ValidationError(
                (
                    "Only PDF, PNG, JPG "
                    "and JPEG files are allowed."
                )
            )

        return receipt




# ============================================================
# EMPLOYEE FINANCIAL PROFILE FORM
# ============================================================

class EmployeeFinancialProfileForm(
    forms.ModelForm
):

    class Meta:

        model = (
            EmployeeFinancialProfile
        )

        fields = [
            "employee_id",
            "full_name",
            "department",
            "position",
            "base_salary_reference",
            "status",
            "notes",
        ]

        widgets = {

            "employee_id":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Example: EMP-001",
                        "autocomplete": "off",
                    }
                ),

            "full_name":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Employee full name",
                        "autocomplete": "off",
                    }
                ),

            "department":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Example: Administration",
                    }
                ),

            "position":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Example: Accountant",
                    }
                ),

            "base_salary_reference":
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": "0.00",
                        "min": "0",
                        "step": "0.01",
                    }
                ),

            "status":
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                ),

            "notes":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder":
                            (
                                "Optional internal "
                                "financial notes..."
                            ),
                    }
                ),
        }

    def clean_employee_id(self):

        employee_id = (
            self.cleaned_data[
                "employee_id"
            ]
            .strip()
        )

        query = (
            EmployeeFinancialProfile
            .objects
            .filter(
                employee_id__iexact=
                    employee_id
            )
        )

        if self.instance.pk:

            query = query.exclude(
                pk=self.instance.pk
            )

        if query.exists():

            raise forms.ValidationError(
                (
                    "An employee financial "
                    "profile with this Employee "
                    "ID already exists."
                )
            )

        return employee_id

    def clean_base_salary_reference(
        self
    ):

        amount = (
            self.cleaned_data.get(
                "base_salary_reference"
            )
        )

        if (
            amount is not None
            and
            amount < 0
        ):

            raise forms.ValidationError(
                (
                    "Base salary reference "
                    "cannot be negative."
                )
            )

        return amount


# ============================================================
# EMPLOYEE FINANCIAL TRANSACTION FORM
# ============================================================

class EmployeeFinancialTransactionForm(
    forms.ModelForm
):

    class Meta:

        model = (
            EmployeeFinancialTransaction
        )

        fields = [
            "employee",
            "transaction_type",
            "amount",
            "transaction_date",
            "payment_method",
            "reference",
            "notes",
        ]

        widgets = {

            "employee":
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                ),

            "transaction_type":
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                ),

            "amount":
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": "0.00",
                        "min": "0.01",
                        "step": "0.01",
                    }
                ),

            "transaction_date":
                forms.DateInput(
                    attrs={
                        "class": "form-control",
                        "type": "date",
                    }
                ),

            "payment_method":
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                ),

            "reference":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            (
                                "Payment, bank or "
                                "document reference"
                            ),
                        "autocomplete": "off",
                    }
                ),

            "notes":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder":
                            (
                                "Describe the financial "
                                "transaction..."
                            ),
                    }
                ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "employee"
        ].queryset = (
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

        self.fields[
            "employee"
        ].empty_label = (
            "Select active employee"
        )

        self.fields[
            "payment_method"
        ].required = False

        self.fields[
            "payment_method"
        ].choices = [
            (
                "",
                "Not applicable / not specified",
            ),
            *
            EmployeeFinancialTransaction
            .PaymentMethod
            .choices,
        ]

    def clean_amount(self):

        amount = (
            self.cleaned_data[
                "amount"
            ]
        )

        if amount <= 0:

            raise forms.ValidationError(
                (
                    "Transaction amount must "
                    "be greater than zero."
                )
            )

        return amount



class ApprovalRequestForm(forms.ModelForm):

    class Meta:

        model = ApprovalRequest

        fields = [
            "operation_type",
            "title",
            "description",
            "amount",
            "related_entity_type",
            "related_entity_id",
            "request_reason",
        ]

        widgets = {

            "operation_type":
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                ),

            "title":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Short approval request title",
                    }
                ),

            "description":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder":
                            "Describe the financial operation...",
                    }
                ),

            "amount":
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "step": "0.01",
                        "min": "0",
                        "placeholder": "0.00",
                    }
                ),

            "related_entity_type":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Example: Expense, Refund, Scholarship",
                    }
                ),

            "related_entity_id":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Related record ID",
                    }
                ),

            "request_reason":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder":
                            "Explain why approval is required...",
                    }
                ),
        }


    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "request_reason"
        ].required = True


    def clean_title(self):

        title = (
            self.cleaned_data
            .get(
                "title",
                "",
            )
            .strip()
        )

        if not title:

            raise forms.ValidationError(
                "Approval request title is required."
            )

        return title


    def clean_request_reason(self):

        reason = (
            self.cleaned_data
            .get(
                "request_reason",
                "",
            )
            .strip()
        )

        if not reason:

            raise forms.ValidationError(
                (
                    "Please provide a reason "
                    "for this approval request."
                )
            )

        return reason


    def clean(self):

        cleaned_data = (
            super().clean()
        )

        amount = (
            cleaned_data.get(
                "amount"
            )
        )

        entity_type = (
            cleaned_data.get(
                "related_entity_type",
                "",
            )
            or ""
        ).strip()

        entity_id = (
            cleaned_data.get(
                "related_entity_id",
                "",
            )
            or ""
        ).strip()

        if (
            amount is not None
            and
            amount < 0
        ):

            self.add_error(
                "amount",
                (
                    "Approval amount cannot "
                    "be negative."
                ),
            )

        # If a related record is specified,
        # both parts must be supplied.
        if (
            entity_type
            and
            not entity_id
        ):

            self.add_error(
                "related_entity_id",
                (
                    "Enter the related record ID "
                    "when an entity type is provided."
                ),
            )

        if (
            entity_id
            and
            not entity_type
        ):

            self.add_error(
                "related_entity_type",
                (
                    "Enter the related entity type "
                    "when a record ID is provided."
                ),
            )

        cleaned_data[
            "related_entity_type"
        ] = entity_type

        cleaned_data[
            "related_entity_id"
        ] = entity_id

        return cleaned_data
import os

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    ExpenseCategory,
    Supplier,
    SupplierBill,
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
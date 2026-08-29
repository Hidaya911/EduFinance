from django import forms

from .models import (
    ExpenseCategory,
    Supplier,
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
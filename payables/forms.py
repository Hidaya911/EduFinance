from django import forms

from .models import ExpenseCategory


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
                    "placeholder": (
                        "Optional description..."
                    ),
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
        name = self.cleaned_data[
            "name"
        ].strip()

        query = ExpenseCategory.objects.filter(
            name__iexact=name
        )

        if self.instance.pk:
            query = query.exclude(
                pk=self.instance.pk
            )

        if query.exists():
            raise forms.ValidationError(
                "An expense category with "
                "this name already exists."
            )

        return name
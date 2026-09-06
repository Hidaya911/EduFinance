from django import forms

from .models import AcademicYear


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear

        fields = [
            "name",
            "is_current",
            "start_date",
            "end_date",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 2026-2027",
                    "autocomplete": "off",
                }
            ),

            "is_current": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get(
            "start_date"
        )

        end_date = cleaned_data.get(
            "end_date"
        )

        if (
            start_date
            and
            end_date
            and
            end_date <= start_date
        ):
            self.add_error(
                "end_date",
                (
                    "End date must be later than "
                    "the start date."
                ),
            )

        return cleaned_data
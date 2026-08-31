from pathlib import Path

from django import forms

from .models import School


class SchoolForm(forms.ModelForm):

    MAX_LOGO_SIZE = (
        5 * 1024 * 1024
    )

    ALLOWED_LOGO_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    class Meta:

        model = School

        fields = [
            "name",
            "logo",
            "address",
            "phone",
            "email",
            "website",
            "default_currency",
            "time_zone",
            "invoice_prefix",
            "receipt_prefix",
            "expense_prefix",
            "current_academic_year",
        ]

        widgets = {

            "name":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "School name",
                    }
                ),

            "address":
                forms.Textarea(
                    attrs={
                        "class":
                            "form-control",
                        "rows": 3,
                        "placeholder":
                            "School address",
                    }
                ),

            "phone":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "+961 ...",
                    }
                ),

            "email":
                forms.EmailInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "finance@school.edu.lb",
                    }
                ),

            "website":
                forms.URLInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "https://...",
                    }
                ),

            "default_currency":
                forms.Select(
                    attrs={
                        "class":
                            "form-control",
                    }
                ),

            "time_zone":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                    }
                ),

            "invoice_prefix":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "INV",
                    }
                ),

            "receipt_prefix":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "REC",
                    }
                ),

            "expense_prefix":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "EXP",
                    }
                ),

            "current_academic_year":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",
                        "placeholder":
                            "2026–2027",
                    }
                ),
        }

    def clean_logo(self):

        logo = (
            self.cleaned_data.get(
                "logo"
            )
        )

        if not logo:
            return logo

        # Existing stored FileField during edit.
        if not hasattr(
            logo,
            "size"
        ):
            return logo

        if (
            logo.size
            >
            self.MAX_LOGO_SIZE
        ):

            raise forms.ValidationError(
                "School logo must not exceed 5 MB."
            )

        extension = (
            Path(
                logo.name
            )
            .suffix
            .lower()
        )

        if (
            extension
            not in
            self.ALLOWED_LOGO_EXTENSIONS
        ):

            raise forms.ValidationError(
                (
                    "School logo must be PNG, "
                    "JPG, JPEG or WEBP."
                )
            )

        return logo
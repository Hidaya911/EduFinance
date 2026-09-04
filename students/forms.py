from django import forms
from .models import Student , Guardian


class StudentForm(forms.ModelForm):
    enrollment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = Student

        fields = [
            "admission_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "email",
            "address",
            "profile_picture",
            "notes",
            "status",
        ]

        widgets = {
            "admission_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "gender": forms.Select(
                attrs={"class": "form-select"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "profile_picture": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Profile picture URL",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

from .models import Student, Guardian


class GuardianForm(forms.ModelForm):

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select",
                "size": "6",
            }
        ),
        help_text="Select one or more students linked to this guardian.",
    )

    primary_student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        help_text="Optional: mark this guardian as primary for one student.",
    )

    class Meta:
        model = Guardian

        fields = [
            "first_name",
            "last_name",
            "relationship",
            "phone",
            "email",
            "address",
            "notes",
            "status",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "relationship": forms.Select(
                attrs={"class": "form-select"}
            ),

            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),

            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_students = Student.objects.filter(
            status="active"
        ).order_by(
            "first_name",
            "last_name",
        )

        self.fields["students"].queryset = active_students

        self.fields[
            "primary_student"
        ].queryset = active_students
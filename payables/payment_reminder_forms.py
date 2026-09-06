from decimal import Decimal

from django import forms

from students.models import (
    Guardian,
    Student,
    StudentGuardian,
)

from .models import PaymentReminder


# ============================================================
# PAYMENT REMINDER FORM
# ============================================================

class PaymentReminderForm(forms.ModelForm):

    # ========================================================
    # STUDENT
    # ========================================================

    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=True,
        empty_label="Select a student",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_student",
                "data-role": "student-select",
            }
        ),
        help_text=(
            "Select the student whose financial obligation "
            "the reminder relates to."
        ),
    )


    # ========================================================
    # GUARDIAN
    # ========================================================

    guardian = forms.ModelChoiceField(
        queryset=Guardian.objects.none(),
        required=False,
        empty_label="Student directly / no guardian",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_guardian",
                "data-role": "guardian-select",
            }
        ),
        help_text=(
            "Optional. If a guardian is selected, they must "
            "already be linked to the selected student."
        ),
    )


    # ========================================================
    # META
    # ========================================================

    class Meta:

        model = PaymentReminder

        fields = [
            "student",
            "guardian",
            "invoice_reference",
            "amount_due",
            "due_date",
            "reminder_date",
            "delivery_method",
            "recipient_name",
            "recipient_email",
            "subject",
            "message",
        ]


        widgets = {

            "invoice_reference":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "e.g. INV-2026-001",
                        "autocomplete": "off",
                    }
                ),

            "amount_due":
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": "0.00",
                        "min": "0.01",
                        "step": "0.01",
                        "inputmode": "decimal",
                    }
                ),

            "due_date":
                forms.DateInput(
                    format="%Y-%m-%d",
                    attrs={
                        "class": "form-control",
                        "type": "date",
                    }
                ),

            "reminder_date":
                forms.DateInput(
                    format="%Y-%m-%d",
                    attrs={
                        "class": "form-control",
                        "type": "date",
                    }
                ),

            "delivery_method":
                forms.Select(
                    attrs={
                        "class": "form-select",
                        "data-role":
                            "delivery-method",
                    }
                ),

            "recipient_name":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Recipient name",
                        "autocomplete": "off",
                    }
                ),

            "recipient_email":
                forms.EmailInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "recipient@example.com",
                        "autocomplete": "email",
                    }
                ),

            "subject":
                forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder":
                            "Payment reminder subject",
                        "autocomplete": "off",
                    }
                ),

            "message":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 7,
                        "placeholder":
                            (
                                "Write the payment "
                                "reminder message..."
                            ),
                    }
                ),
        }


        help_texts = {

            "invoice_reference":
                (
                    "Temporary invoice reference until the "
                    "shared Student Invoice model is integrated."
                ),

            "amount_due":
                (
                    "Outstanding amount represented by this "
                    "reminder snapshot."
                ),

            "due_date":
                (
                    "Due date of the financial obligation."
                ),

            "reminder_date":
                (
                    "Date associated with this reminder record."
                ),

            "delivery_method":
                (
                    "Initial EduFinance channels are "
                    "In-System Notification and Email."
                ),

            "recipient_name":
                (
                    "A snapshot of the intended recipient name."
                ),

            "recipient_email":
                (
                    "Required when Email is selected."
                ),

            "subject":
                (
                    "Subject stored with the reminder history."
                ),

            "message":
                (
                    "Message stored exactly with this "
                    "financial reminder record."
                ),
        }


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )


        # ----------------------------------------------------
        # STUDENTS
        # ----------------------------------------------------

        self.fields[
            "student"
        ].queryset = (
            Student.objects
            .filter(
                status="active",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )


        # Human-friendly student labels.
        self.fields[
            "student"
        ].label_from_instance = (
            self._student_label
        )


        # ----------------------------------------------------
        # GUARDIANS
        # ----------------------------------------------------

        self.fields[
            "guardian"
        ].queryset = (
            Guardian.objects
            .filter(
                status="active",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )


        self.fields[
            "guardian"
        ].label_from_instance = (
            self._guardian_label
        )


        # ----------------------------------------------------
        # DATE FORMATTING
        # ----------------------------------------------------

        if (
            self.instance
            and
            self.instance.pk
        ):

            if self.instance.due_date:

                self.initial[
                    "due_date"
                ] = (
                    self.instance
                    .due_date
                    .isoformat()
                )

            if self.instance.reminder_date:

                self.initial[
                    "reminder_date"
                ] = (
                    self.instance
                    .reminder_date
                    .isoformat()
                )


    # ========================================================
    # DISPLAY LABELS
    # ========================================================

    @staticmethod
    def _student_label(
        student,
    ):

        student_number = (
            student.student_number
            or ""
        ).strip()

        name = (
            student.full_name
            or ""
        ).strip()

        if student_number:

            return (
                f"{student_number} — {name}"
            )

        return name


    @staticmethod
    def _guardian_label(
        guardian,
    ):

        name = (
            guardian.full_name
            or ""
        ).strip()

        relationship = (
            guardian
            .get_relationship_display()
        )

        email = (
            guardian.email
            or ""
        ).strip()

        label = (
            f"{name} — {relationship}"
        )

        if email:

            label += (
                f" — {email}"
            )

        return label


    # ========================================================
    # INVOICE REFERENCE
    # ========================================================

    def clean_invoice_reference(
        self,
    ):

        value = (
            self.cleaned_data[
                "invoice_reference"
            ]
            or ""
        ).strip()

        if not value:

            raise forms.ValidationError(
                "Invoice reference is required."
            )

        return value


    # ========================================================
    # AMOUNT
    # ========================================================

    def clean_amount_due(
        self,
    ):

        amount = (
            self.cleaned_data[
                "amount_due"
            ]
        )

        if (
            amount is None
            or
            amount
            <= Decimal("0.00")
        ):

            raise forms.ValidationError(
                (
                    "Amount due must be "
                    "greater than zero."
                )
            )

        return amount


    # ========================================================
    # SUBJECT
    # ========================================================

    def clean_subject(
        self,
    ):

        value = (
            self.cleaned_data[
                "subject"
            ]
            or ""
        ).strip()

        if not value:

            raise forms.ValidationError(
                "Reminder subject is required."
            )

        return value


    # ========================================================
    # MESSAGE
    # ========================================================

    def clean_message(
        self,
    ):

        value = (
            self.cleaned_data[
                "message"
            ]
            or ""
        ).strip()

        if not value:

            raise forms.ValidationError(
                "Reminder message is required."
            )

        return value


    # ========================================================
    # COMPLETE FORM VALIDATION
    # ========================================================

    def clean(
        self,
    ):

        cleaned_data = (
            super().clean()
        )


        student = (
            cleaned_data.get(
                "student"
            )
        )

        guardian = (
            cleaned_data.get(
                "guardian"
            )
        )

        delivery_method = (
            cleaned_data.get(
                "delivery_method"
            )
        )

        recipient_name = (
            cleaned_data.get(
                "recipient_name"
            )
            or ""
        ).strip()

        recipient_email = (
            cleaned_data.get(
                "recipient_email"
            )
            or ""
        ).strip()


        # ----------------------------------------------------
        # GUARDIAN RELATIONSHIP
        # ----------------------------------------------------

        if (
            student
            and
            guardian
        ):

            linked = (
                StudentGuardian.objects
                .filter(
                    student_id=str(
                        student.pk
                    ),
                    guardian_id=str(
                        guardian.pk
                    ),
                )
                .exists()
            )

            if not linked:

                self.add_error(
                    "guardian",
                    (
                        "The selected guardian "
                        "is not linked to this "
                        "student."
                    ),
                )


        # ----------------------------------------------------
        # DEFAULT RECIPIENT SNAPSHOT
        # ----------------------------------------------------

        if guardian:

            if not recipient_name:

                recipient_name = (
                    guardian.full_name
                    or ""
                ).strip()

                cleaned_data[
                    "recipient_name"
                ] = recipient_name


            if not recipient_email:

                recipient_email = (
                    guardian.email
                    or ""
                ).strip()

                cleaned_data[
                    "recipient_email"
                ] = recipient_email


        elif student:

            if not recipient_name:

                recipient_name = (
                    student.full_name
                    or ""
                ).strip()

                cleaned_data[
                    "recipient_name"
                ] = recipient_name


            if not recipient_email:

                recipient_email = (
                    student.email
                    or ""
                ).strip()

                cleaned_data[
                    "recipient_email"
                ] = recipient_email


        # ----------------------------------------------------
        # EMAIL REQUIREMENT
        # ----------------------------------------------------

        if (
            delivery_method
            ==
            PaymentReminder
            .DeliveryMethod
            .EMAIL
            and
            not recipient_email
        ):

            self.add_error(
                "recipient_email",
                (
                    "An email address is "
                    "required when Email "
                    "delivery is selected."
                ),
            )


        return cleaned_data


    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        commit=True,
    ):

        reminder = (
            super()
            .save(
                commit=False
            )
        )


        # ----------------------------------------------------
        # APPLY NORMALIZED / DERIVED VALUES
        # ----------------------------------------------------

        reminder.invoice_reference = (
            self.cleaned_data[
                "invoice_reference"
            ]
            or ""
        ).strip()


        reminder.recipient_name = (
            self.cleaned_data.get(
                "recipient_name"
            )
            or ""
        ).strip()


        reminder.recipient_email = (
            self.cleaned_data.get(
                "recipient_email"
            )
            or ""
        ).strip()


        reminder.subject = (
            self.cleaned_data[
                "subject"
            ]
            or ""
        ).strip()


        reminder.message = (
            self.cleaned_data[
                "message"
            ]
            or ""
        ).strip()


        if commit:

            reminder.full_clean()

            reminder.save()


        return reminder
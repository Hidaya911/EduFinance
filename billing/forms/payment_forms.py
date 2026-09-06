from django import forms
from django.forms import formset_factory
from django.utils import timezone

from billing.models import Invoice, Payment
from students.models import Student


class PaymentForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    payment_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    payment_method = forms.ChoiceField(
        choices=Payment.METHOD_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        ),
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["student"].queryset = Student.objects.filter(
            status="active"
        ).order_by("first_name", "last_name")


class PaymentAllocationForm(forms.Form):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    amount = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }
        ),
    )

    def __init__(self, *args, school=None, student=None, **kwargs):
        super().__init__(*args, **kwargs)

        qs = Invoice.objects.filter(
            status__in=[
                "unpaid",
                "partially_paid",
                "overdue",
            ]
        )

        if school:
            qs = qs.filter(school=school)

        if student:
            qs = qs.filter(student=student)

        self.fields["invoice"].queryset = qs.order_by("due_date")


PaymentAllocationFormSet = formset_factory(
    PaymentAllocationForm,
    extra=1,
    can_delete=True,
)
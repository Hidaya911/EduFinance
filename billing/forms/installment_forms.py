from decimal import Decimal
from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from billing.models import InstallmentPlan, Installment, Invoice
class InstallmentPlanForm(forms.ModelForm):
    class Meta:
        model=InstallmentPlan; fields=["invoice","total_amount"]
        widgets={"invoice":forms.Select(attrs={"class":"form-select"}),"total_amount":forms.NumberInput(attrs={"class":"form-control","min":"0.01","step":"0.01"})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.fields["invoice"].queryset=Invoice.objects.exclude(status__in=[Invoice.STATUS_PAID,Invoice.STATUS_VOID]).filter(balance__gt=0).order_by("due_date")
    def clean(self):
        c=super().clean(); i=c.get("invoice"); t=c.get("total_amount")
        if i and t and t>i.balance: self.add_error("total_amount","Plan total cannot exceed the invoice balance.")
        return c
class BaseInstallmentFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        total=Decimal("0.00"); count=0
        for f in self.forms:
            d=getattr(f,"cleaned_data",None)
            if not d or d.get("DELETE"): continue
            if d.get("amount") and d.get("due_date"): count+=1; total+=d["amount"]
        if count==0: raise forms.ValidationError("Add at least one installment.")
        if self.instance.total_amount and total!=self.instance.total_amount: raise forms.ValidationError(f"Installments total ({total}) must equal plan total ({self.instance.total_amount}).")
class InstallmentForm(forms.ModelForm):
    class Meta:
        model=Installment; fields=["due_date","amount"]
        widgets={"due_date":forms.DateInput(attrs={"class":"form-control","type":"date"}),"amount":forms.NumberInput(attrs={"class":"form-control","min":"0.01","step":"0.01"})}
InstallmentFormSet=inlineformset_factory(InstallmentPlan,Installment,form=InstallmentForm,formset=BaseInstallmentFormSet,extra=2,can_delete=True)

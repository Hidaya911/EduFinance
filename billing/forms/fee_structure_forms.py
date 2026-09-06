from django import forms
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from billing.models import FeeStructure, FeeStructureItem
from school_config.models import FeeCategory
class FeeStructureForm(forms.ModelForm):
    class Meta:
        model=FeeStructure; fields=["name","academic_year","grade","is_active"]
        widgets={"name":forms.TextInput(attrs={"class":"form-control"}),"academic_year":forms.Select(attrs={"class":"form-select"}),"grade":forms.Select(attrs={"class":"form-select"}),"is_active":forms.CheckboxInput(attrs={"class":"form-check-input"})}
    def clean_name(self): return self.cleaned_data["name"].strip()
class BaseFeeStructureItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        cats=set(); count=0
        for f in self.forms:
            d=getattr(f,"cleaned_data",None)
            if not d or d.get("DELETE"): continue
            c=d.get("fee_category"); a=d.get("amount")
            if not c and not a: continue
            count+=1
            if c:
                if c.pk in cats: raise forms.ValidationError("The same fee category cannot be added twice.")
                cats.add(c.pk)
        if count==0: raise forms.ValidationError("Add at least one fee item.")
class FeeStructureItemForm(forms.ModelForm):
    class Meta:
        model=FeeStructureItem; fields=["fee_category","amount"]
        widgets={"fee_category":forms.Select(attrs={"class":"form-select"}),"amount":forms.NumberInput(attrs={"class":"form-control","min":"0.01","step":"0.01"})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance and self.instance.pk and self.instance.fee_category_id: self.fields["fee_category"].queryset=FeeCategory.objects.filter(Q(is_active=True)|Q(pk=self.instance.fee_category_id)).order_by("name")
        else: self.fields["fee_category"].queryset=FeeCategory.objects.filter(is_active=True).order_by("name")
FeeStructureItemFormSet=inlineformset_factory(FeeStructure,FeeStructureItem,form=FeeStructureItemForm,formset=BaseFeeStructureItemFormSet,extra=1,can_delete=True)

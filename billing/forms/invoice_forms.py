from django import forms
from billing.models import Invoice, FeeStructure
from students.models import Student, Enrollment
class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model=Invoice; fields=["student","enrollment","academic_year","fee_structure","due_date"]
        widgets={"student":forms.Select(attrs={"class":"form-select"}),"enrollment":forms.Select(attrs={"class":"form-select"}),"academic_year":forms.Select(attrs={"class":"form-select"}),"fee_structure":forms.Select(attrs={"class":"form-select"}),"due_date":forms.DateInput(attrs={"class":"form-control","type":"date"})}
    def __init__(self,*args,school=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["student"].queryset=Student.objects.filter(status="active").order_by("first_name","last_name")
        self.fields["enrollment"].queryset=Enrollment.objects.filter(status="active")
        if school: self.fields["fee_structure"].queryset=FeeStructure.objects.filter(school=school,is_active=True).order_by("name")
    def clean(self):
        c=super().clean(); s=c.get("student"); e=c.get("enrollment"); y=c.get("academic_year"); f=c.get("fee_structure")
        if s and e and str(e.student_id)!=str(s.pk): self.add_error("enrollment","This enrollment does not belong to the selected student.")
        if f and y and f.academic_year_id!=y.pk: self.add_error("fee_structure","Fee structure and academic year must match.")
        return c

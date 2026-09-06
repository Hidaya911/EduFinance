from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from accounts.core.models import AcademicYear
from school_config.models import School
from students.models import Student
from .invoice import Invoice

class InstallmentPlan(models.Model):
    STATUS_CHOICES=[("active","Active"),("completed","Completed"),("cancelled","Cancelled")]
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="installment_plans")
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="installment_plans")
    invoice=models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name="installment_plans")
    academic_year=models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name="installment_plans")
    total_amount=models.DecimalField(max_digits=14,decimal_places=2)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="active")
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="created_installment_plans")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table="installment_plans"; ordering=["-created_at"]
    def __str__(self): return f"{self.student.full_name} - {self.invoice.invoice_number}"
    def clean(self):
        super().clean()
        if self.total_amount<=0: raise ValidationError({"total_amount":"Total amount must be greater than zero."})
        if self.invoice_id and self.student_id and self.invoice.student_id!=self.student_id: raise ValidationError("Invoice and installment plan student must match.")

class Installment(models.Model):
    STATUS_CHOICES=[("pending","Pending"),("partially_paid","Partially Paid"),("paid","Paid"),("overdue","Overdue")]
    plan=models.ForeignKey(InstallmentPlan,on_delete=models.CASCADE,related_name="installments")
    installment_number=models.PositiveIntegerField()
    due_date=models.DateField()
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    paid_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    class Meta:
        db_table="installments"; ordering=["due_date","installment_number"]
        constraints=[models.UniqueConstraint(fields=["plan","installment_number"],name="unique_installment_number_per_plan")]
    def clean(self):
        super().clean()
        if self.amount<=0: raise ValidationError({"amount":"Installment amount must be greater than zero."})
        if self.paid_amount<0 or self.paid_amount>self.amount: raise ValidationError({"paid_amount":"Paid amount must be between zero and the installment amount."})
    def refresh_status(self):
        if self.paid_amount>=self.amount: self.status="paid"
        elif self.paid_amount>0: self.status="partially_paid"
        elif self.due_date<timezone.localdate(): self.status="overdue"
        else: self.status="pending"
        Installment.objects.filter(pk=self.pk).update(status=self.status)
    def __str__(self): return f"{self.plan} - #{self.installment_number}"

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from accounts.core.models import AcademicYear
from school_config.models import FeeCategory, School
from students.models import Student, Enrollment
from .fee_structure import FeeStructure

class Invoice(models.Model):
    STATUS_DRAFT="draft"; STATUS_UNPAID="unpaid"; STATUS_PARTIAL="partially_paid"; STATUS_PAID="paid"; STATUS_OVERDUE="overdue"; STATUS_VOID="void"
    STATUS_CHOICES=[(STATUS_DRAFT,"Draft"),(STATUS_UNPAID,"Unpaid"),(STATUS_PARTIAL,"Partially Paid"),(STATUS_PAID,"Paid"),(STATUS_OVERDUE,"Overdue"),(STATUS_VOID,"Void")]
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="invoices")
    invoice_number=models.CharField(max_length=80,unique=True)
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="invoices")
    enrollment=models.ForeignKey(Enrollment,on_delete=models.PROTECT,related_name="invoices")
    academic_year=models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name="invoices")
    fee_structure=models.ForeignKey(FeeStructure,on_delete=models.PROTECT,related_name="invoices",null=True,blank=True)
    total_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
    paid_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
    balance=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
    status=models.CharField(max_length=30,choices=STATUS_CHOICES,default=STATUS_UNPAID)
    due_date=models.DateField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="created_invoices")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        db_table="invoices"; ordering=["-created_at"]
    def __str__(self): return self.invoice_number
    def clean(self):
        super().clean()
        if self.total_amount < 0 or self.paid_amount < 0 or self.balance < 0: raise ValidationError("Invoice amounts cannot be negative.")
        if self.enrollment_id and str(self.enrollment.student_id) != str(self.student_id): raise ValidationError({"enrollment":"The selected enrollment does not belong to this student."})
    def refresh_financial_status(self):
        if self.status==self.STATUS_VOID: return
        self.balance=max(self.total_amount-self.paid_amount,Decimal("0.00"))
        if self.balance==0 and self.total_amount>0: self.status=self.STATUS_PAID
        elif self.paid_amount>0: self.status=self.STATUS_PARTIAL
        elif self.due_date and self.due_date<timezone.localdate(): self.status=self.STATUS_OVERDUE
        else: self.status=self.STATUS_UNPAID
        Invoice.objects.filter(pk=self.pk).update(paid_amount=self.paid_amount,balance=self.balance,status=self.status)

class InvoiceItem(models.Model):
    invoice=models.ForeignKey(Invoice,on_delete=models.CASCADE,related_name="items")
    fee_category=models.ForeignKey(FeeCategory,on_delete=models.PROTECT,related_name="invoice_items",null=True,blank=True)
    category_name=models.CharField(max_length=150)
    description=models.CharField(max_length=255,blank=True)
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    class Meta: db_table="invoice_items"
    def clean(self):
        super().clean()
        if self.amount<=0: raise ValidationError({"amount":"Amount must be greater than zero."})
    def __str__(self): return f"{self.invoice.invoice_number} - {self.category_name}"

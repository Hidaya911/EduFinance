from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from school_config.models import School
from students.models import Student
from .invoice import Invoice

class Payment(models.Model):
    METHOD_CHOICES=[("cash","Cash"),("card","Card"),("bank_transfer","Bank Transfer"),("check","Check"),("other","Other")]
    STATUS_CHOICES=[("completed","Completed"),("void","Void")]
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="payments")
    payment_number=models.CharField(max_length=80,unique=True)
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="payments")
    payment_date=models.DateField()
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    payment_method=models.CharField(max_length=30,choices=METHOD_CHOICES)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="completed")
    received_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="received_payments")
    notes=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table="payments"; ordering=["-payment_date","-created_at"]
    def __str__(self): return self.payment_number
    def clean(self):
        super().clean()
        if self.amount is None or self.amount<=0: raise ValidationError({"amount":"Payment amount must be greater than zero."})

class PaymentAllocation(models.Model):
    payment=models.ForeignKey(Payment,on_delete=models.CASCADE,related_name="allocations")
    invoice=models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name="allocations")
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    class Meta: db_table="payment_allocations"
    def clean(self):
        super().clean()
        if self.amount is None or self.amount<=0: raise ValidationError({"amount":"Allocation amount must be greater than zero."})
        if self.invoice_id and self.payment_id:
            if self.invoice.student_id != self.payment.student_id: raise ValidationError("Payment and invoice must belong to the same student.")
            if self.invoice.status==Invoice.STATUS_VOID: raise ValidationError("Cannot allocate a payment to a void invoice.")
    def __str__(self): return f"{self.payment.payment_number} -> {self.invoice.invoice_number}"

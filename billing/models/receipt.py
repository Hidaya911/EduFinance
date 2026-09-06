from django.db import models
from school_config.models import School
from students.models import Student
from .payment import Payment

class Receipt(models.Model):
    STATUS_CHOICES=[("issued","Issued"),("void","Void")]
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="receipts")
    receipt_number=models.CharField(max_length=80,unique=True)
    payment=models.OneToOneField(Payment,on_delete=models.PROTECT,related_name="receipt")
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="receipts")
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    issued_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="issued")
    class Meta: db_table="receipts"; ordering=["-issued_at"]
    def __str__(self): return self.receipt_number

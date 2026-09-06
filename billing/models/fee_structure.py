from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from accounts.core.models import AcademicYear
from school_config.models import FeeCategory, Grade, School

class FeeStructure(models.Model):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="fee_structures")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="fee_structures")
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="fee_structures")
    name = models.CharField(max_length=150)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), editable=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_fee_structures")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "fee_structures"
        ordering = ["-created_at"]
    def __str__(self): return f"{self.name} - {self.grade.name}"
    def recalculate_total(self):
        total = sum((item.amount for item in self.items.all()), Decimal("0.00"))
        FeeStructure.objects.filter(pk=self.pk).update(total_amount=total)
        self.total_amount = total

class FeeStructureItem(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="items")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="fee_structure_items")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    class Meta:
        db_table = "fee_structure_items"
        constraints=[models.UniqueConstraint(fields=["fee_structure","fee_category"], name="unique_fee_category_per_structure")]
    def __str__(self): return f"{self.fee_structure.name} - {self.fee_category.name}"
    def clean(self):
        super().clean()
        if self.amount is None or self.amount <= 0: raise ValidationError({"amount":"Amount must be greater than zero."})
        if self.fee_category_id and not self.fee_category.is_active: raise ValidationError({"fee_category":"Inactive fee categories cannot be used."})
    def save(self,*args,**kwargs):
        self.full_clean(); super().save(*args,**kwargs)
        if self.fee_structure_id: self.fee_structure.recalculate_total()
    def delete(self,*args,**kwargs):
        structure=self.fee_structure; super().delete(*args,**kwargs)
        if structure.pk: structure.recalculate_total()

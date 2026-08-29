from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ============================================================
# EXPENSE CATEGORY
# ============================================================

class ExpenseCategory(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "expense_categories"
        ordering = ["name"]

        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


# ============================================================
# SUPPLIER
# ============================================================

class Supplier(models.Model):

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    contact_person = models.CharField(
        max_length=120,
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    tax_number = models.CharField(
        max_length=60,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "suppliers"
        ordering = ["name"]

        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.name


# ============================================================
# SUPPLIER BILL
# IMPORTANT:
# This class must be OUTSIDE the Supplier class.
# ============================================================

class SupplierBill(models.Model):

    class Status(models.TextChoices):

        UNPAID = (
            "unpaid",
            "Unpaid",
        )

        PARTIALLY_PAID = (
            "partially_paid",
            "Partially Paid",
        )

        PAID = (
            "paid",
            "Paid",
        )

        OVERDUE = (
            "overdue",
            "Overdue",
        )

        CANCELLED = (
            "cancelled",
            "Cancelled",
        )

    bill_number = models.CharField(
        max_length=60,
        unique=True,
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="bills",
    )

    bill_date = models.DateField()

    due_date = models.DateField()

    description = models.TextField()

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    amount_paid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )

    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.UNPAID,
    )

    document = models.FileField(
        upload_to="supplier_bills/%Y/%m/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "supplier_bills"

        ordering = [
            "-bill_date",
            "-created_at",
        ]

        verbose_name = "Supplier Bill"
        verbose_name_plural = "Supplier Bills"

    def __str__(self):

        return (
            f"{self.bill_number} - "
            f"{self.supplier.name}"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def clean(self):

        super().clean()

        if (
            self.total_amount is not None
            and self.total_amount <= 0
        ):

            raise ValidationError(
                {
                    "total_amount":
                        "Bill total must be greater than zero."
                }
            )

        if (
            self.amount_paid is not None
            and self.amount_paid < 0
        ):

            raise ValidationError(
                {
                    "amount_paid":
                        "Amount paid cannot be negative."
                }
            )

        if (
            self.total_amount is not None
            and self.amount_paid is not None
            and self.amount_paid
            > self.total_amount
        ):

            raise ValidationError(
                {
                    "total_amount":
                        (
                            "Bill total cannot be less "
                            "than the amount already paid."
                        )
                }
            )

        if (
            self.bill_date
            and self.due_date
            and self.due_date
            < self.bill_date
        ):

            raise ValidationError(
                {
                    "due_date":
                        (
                            "Due date cannot be earlier "
                            "than the bill date."
                        )
                }
            )

    # ========================================================
    # AUTOMATIC FINANCIAL STATE
    # ========================================================

    def calculate_financial_state(self):

        total = (
            self.total_amount
            or Decimal("0.00")
        )

        paid = (
            self.amount_paid
            or Decimal("0.00")
        )

        remaining = (
            total - paid
        )

        if remaining < 0:
            remaining = Decimal("0.00")

        self.remaining_amount = remaining

        # -----------------------------------------------
        # Preserve cancellation
        # -----------------------------------------------

        if (
            self.status
            == self.Status.CANCELLED
        ):
            return

        # -----------------------------------------------
        # Paid
        # -----------------------------------------------

        if remaining <= 0:

            self.status = (
                self.Status.PAID
            )

            return

        # -----------------------------------------------
        # Overdue
        # -----------------------------------------------

        if (
            self.due_date
            and self.due_date
            < timezone.localdate()
        ):

            self.status = (
                self.Status.OVERDUE
            )

            return

        # -----------------------------------------------
        # Partially Paid
        # -----------------------------------------------

        if paid > 0:

            self.status = (
                self.Status.PARTIALLY_PAID
            )

            return

        # -----------------------------------------------
        # Unpaid
        # -----------------------------------------------

        self.status = (
            self.Status.UNPAID
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        *args,
        **kwargs,
    ):

        self.calculate_financial_state()

        super().save(
            *args,
            **kwargs,
        )
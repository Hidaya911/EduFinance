import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone







def generate_supplier_payment_number():

    date_part = (
        timezone.localdate()
        .strftime("%Y%m%d")
    )

    random_part = (
        uuid.uuid4()
        .hex[:6]
        .upper()
    )

    return (
        f"SPAY-{date_part}-{random_part}"
    )









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



# ============================================================
# SUPPLIER PAYMENT
# ============================================================

class SupplierPayment(models.Model):

    class PaymentMethod(models.TextChoices):

        CASH = (
            "cash",
            "Cash",
        )

        BANK_TRANSFER = (
            "bank_transfer",
            "Bank Transfer",
        )

        CHEQUE = (
            "cheque",
            "Cheque",
        )

        CARD = (
            "card",
            "Card",
        )

        OTHER = (
            "other",
            "Other",
        )

    class Status(models.TextChoices):

        POSTED = (
            "posted",
            "Posted",
        )

        VOIDED = (
            "voided",
            "Voided",
        )

    payment_number = models.CharField(
        max_length=40,
        unique=True,
        default=generate_supplier_payment_number,
        editable=False,
    )

    bill = models.ForeignKey(
        SupplierBill,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="payments",
        editable=False,
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
    )

    reference = models.CharField(
        max_length=120,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.POSTED,
        editable=False,
    )

    void_reason = models.TextField(
        blank=True,
    )

    voided_at = models.DateTimeField(
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

        db_table = "supplier_payments"

        ordering = [
            "-payment_date",
            "-created_at",
        ]

        verbose_name = "Supplier Payment"

        verbose_name_plural = "Supplier Payments"

    def __str__(self):

        return (
            f"{self.payment_number} - "
            f"{self.supplier.name}"
        )

    def clean(self):

        super().clean()

        if (
            self.amount is None
            or self.amount <= 0
        ):

            raise ValidationError(
                {
                    "amount":
                        (
                            "Payment amount must "
                            "be greater than zero."
                        )
                }
            )

        if not self.bill_id:
            return

        # Only validate the bill balance
        # when creating a new posted payment.
        if (
            self._state.adding
            and self.status
            == self.Status.POSTED
        ):

            if (
                self.bill.status
                == SupplierBill.Status.CANCELLED
            ):

                raise ValidationError(
                    {
                        "bill":
                            (
                                "Payments cannot be "
                                "recorded against a "
                                "cancelled bill."
                            )
                    }
                )

            if (
                self.bill.remaining_amount
                <= Decimal("0.00")
            ):

                raise ValidationError(
                    {
                        "bill":
                            (
                                "This supplier bill "
                                "is already fully paid."
                            )
                    }
                )

            if (
                self.amount
                > self.bill.remaining_amount
            ):

                raise ValidationError(
                    {
                        "amount":
                            (
                                "Payment amount cannot "
                                "be greater than the "
                                "bill's remaining balance."
                            )
                    }
                )



# ============================================================
# EXPENSE NUMBER GENERATOR
# ============================================================

def generate_expense_number():

    from school_config.models import School

    school = (
        School.objects
        .first()
    )

    prefix = "EXP"

    if (
        school
        and
        school.expense_prefix
    ):

        prefix = (
            school.expense_prefix
            .strip()
            .upper()
        )

    date_part = (
        timezone.localdate()
        .strftime("%Y%m%d")
    )

    random_part = (
        uuid.uuid4()
        .hex[:6]
        .upper()
    )

    return (
        f"{prefix}-"
        f"{date_part}-"
        f"{random_part}"
    )


# ============================================================
# EXPENSE
# ============================================================

class Expense(models.Model):

    class PaymentMethod(models.TextChoices):

        CASH = (
            "cash",
            "Cash",
        )

        BANK_TRANSFER = (
            "bank_transfer",
            "Bank Transfer",
        )

        CHEQUE = (
            "cheque",
            "Cheque",
        )

        CARD = (
            "card",
            "Card",
        )

        OTHER = (
            "other",
            "Other",
        )

    class ApprovalStatus(models.TextChoices):

        NOT_REQUIRED = (
            "not_required",
            "Not Required",
        )

        PENDING = (
            "pending",
            "Pending",
        )

        APPROVED = (
            "approved",
            "Approved",
        )

        REJECTED = (
            "rejected",
            "Rejected",
        )

    class RecordStatus(models.TextChoices):

        ACTIVE = (
            "active",
            "Active",
        )

        VOIDED = (
            "voided",
            "Voided",
        )

    expense_number = models.CharField(
        max_length=40,
        unique=True,
        default=generate_expense_number,
        editable=False,
    )

    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="expenses",
        blank=True,
        null=True,
    )

    description = models.TextField()

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    expense_date = models.DateField()

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
    )

    reference = models.CharField(
        max_length=120,
        blank=True,
    )

    receipt = models.FileField(
        upload_to="expenses/%Y/%m/",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="created_expenses",
    )

    approval_status = models.CharField(
        max_length=25,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
    )

    record_status = models.CharField(
        max_length=20,
        choices=RecordStatus.choices,
        default=RecordStatus.ACTIVE,
        editable=False,
    )

    void_reason = models.TextField(
        blank=True,
    )

    voided_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    voided_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="voided_expenses",
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

        db_table = "expenses"

        ordering = [
            "-expense_date",
            "-created_at",
        ]

        verbose_name = "Expense"

        verbose_name_plural = "Expenses"

    def __str__(self):

        return (
            f"{self.expense_number} - "
            f"{self.description[:40]}"
        )

    def clean(self):

        super().clean()

        if (
            self.amount is None
            or self.amount <= 0
        ):

            raise ValidationError(
                {
                    "amount":
                        (
                            "Expense amount must "
                            "be greater than zero."
                        )
                }
            )

        if (
            self.category_id
            and
            not self.category.is_active
        ):

            raise ValidationError(
                {
                    "category":
                        (
                            "Inactive expense categories "
                            "cannot be used for new expenses."
                        )
                }
            )

        if (
            self.supplier_id
            and
            not self.supplier.is_active
        ):

            raise ValidationError(
                {
                    "supplier":
                        (
                            "Inactive suppliers cannot "
                            "be used for new expenses."
                        )
                }
            )



# ============================================================
# EMPLOYEE FINANCIAL TRANSACTION NUMBER
# ============================================================

def generate_employee_financial_transaction_number():

    date_part = (
        timezone.localdate()
        .strftime("%Y%m%d")
    )

    random_part = (
        uuid.uuid4()
        .hex[:6]
        .upper()
    )

    return (
        f"EFT-{date_part}-{random_part}"
    )


# ============================================================
# EMPLOYEE FINANCIAL PROFILE
# ============================================================

class EmployeeFinancialProfile(models.Model):

    class Status(models.TextChoices):

        ACTIVE = (
            "active",
            "Active",
        )

        INACTIVE = (
            "inactive",
            "Inactive",
        )

    employee_id = models.CharField(
        max_length=50,
        unique=True,
    )

    full_name = models.CharField(
        max_length=160,
    )

    department = models.CharField(
        max_length=120,
        blank=True,
    )

    position = models.CharField(
        max_length=120,
        blank=True,
    )

    base_salary_reference = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )

    notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "employee_financial_profiles"

        ordering = [
            "full_name",
        ]

        verbose_name = (
            "Employee Financial Profile"
        )

        verbose_name_plural = (
            "Employee Financial Profiles"
        )

    def __str__(self):

        return (
            f"{self.employee_id} - "
            f"{self.full_name}"
        )


# ============================================================
# EMPLOYEE FINANCIAL TRANSACTION
# ============================================================

class EmployeeFinancialTransaction(models.Model):

    class TransactionType(models.TextChoices):

        ADVANCE = (
            "advance",
            "Financial Advance",
        )

        REIMBURSEMENT = (
            "reimbursement",
            "Reimbursement",
        )

        ALLOWANCE = (
            "allowance",
            "Allowance",
        )

        DEDUCTION = (
            "deduction",
            "Deduction",
        )

        PAYMENT = (
            "payment",
            "Payment",
        )

    class PaymentMethod(models.TextChoices):

        CASH = (
            "cash",
            "Cash",
        )

        BANK_TRANSFER = (
            "bank_transfer",
            "Bank Transfer",
        )

        CHEQUE = (
            "cheque",
            "Cheque",
        )

        CARD = (
            "card",
            "Card",
        )

        OTHER = (
            "other",
            "Other",
        )

    class Status(models.TextChoices):

        POSTED = (
            "posted",
            "Posted",
        )

        VOIDED = (
            "voided",
            "Voided",
        )

    transaction_number = models.CharField(
        max_length=40,
        unique=True,
        default=
            generate_employee_financial_transaction_number,
        editable=False,
    )

    employee = models.ForeignKey(
        EmployeeFinancialProfile,
        on_delete=models.PROTECT,
        related_name="financial_transactions",
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    transaction_date = models.DateField()

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        blank=True,
    )

    reference = models.CharField(
        max_length=120,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name=
            "created_employee_financial_transactions",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.POSTED,
        editable=False,
    )

    void_reason = models.TextField(
        blank=True,
    )

    voided_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    voided_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name=
            "voided_employee_financial_transactions",
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

        db_table = (
            "employee_financial_transactions"
        )

        ordering = [
            "-transaction_date",
            "-created_at",
        ]

        verbose_name = (
            "Employee Financial Transaction"
        )

        verbose_name_plural = (
            "Employee Financial Transactions"
        )

    def __str__(self):

        return (
            f"{self.transaction_number} - "
            f"{self.employee.full_name}"
        )

    def clean(self):

        super().clean()

        if (
            self.amount is None
            or self.amount <= 0
        ):

            raise ValidationError(
                {
                    "amount":
                        (
                            "Transaction amount must "
                            "be greater than zero."
                        )
                }
            )

        if (
            self.employee_id
            and
            self.employee.status
            !=
            EmployeeFinancialProfile.Status.ACTIVE
        ):

            raise ValidationError(
                {
                    "employee":
                        (
                            "New financial transactions "
                            "cannot be recorded for an "
                            "inactive employee."
                        )
                }
            )
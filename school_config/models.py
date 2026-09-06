from django.core.exceptions import ValidationError
from django.db import models


class School(models.Model):

    class Currency(models.TextChoices):
        USD = "USD", "USD — US Dollar"
        LBP = "LBP", "LBP — Lebanese Pound"

    # ========================================================
    # SCHOOL IDENTITY
    # ========================================================

    name = models.CharField(
        max_length=200,
    )

    logo = models.FileField(
        upload_to="school/logos/",
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    # ========================================================
    # FINANCIAL CONFIGURATION
    # ========================================================

    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
    )

    time_zone = models.CharField(
        max_length=60,
        default="Asia/Beirut",
    )

    invoice_prefix = models.CharField(
        max_length=15,
        default="INV",
    )

    receipt_prefix = models.CharField(
        max_length=15,
        default="REC",
    )

    expense_prefix = models.CharField(
        max_length=15,
        default="EXP",
    )

    # Temporary until the AcademicYear model exists.
    # Later we will migrate this to a ForeignKey.
    current_academic_year = models.CharField(
        max_length=30,
        blank=True,
    )

    # ========================================================
    # SYSTEM FIELDS
    # ========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "school"
        verbose_name = "School"
        verbose_name_plural = "School"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        # EduFinance currently represents one school installation.
        existing = School.objects.all()

        if self.pk:
            existing = existing.exclude(
                pk=self.pk
            )

        if existing.exists():
            raise ValidationError(
                "Only one school configuration may exist."
            )

        prefixes = {
            "invoice_prefix": self.invoice_prefix,
            "receipt_prefix": self.receipt_prefix,
            "expense_prefix": self.expense_prefix,
        }

        errors = {}

        for field_name, value in prefixes.items():

            cleaned = (
                value.strip().upper()
                if value
                else ""
            )

            if not cleaned:
                errors[field_name] = (
                    "Prefix cannot be empty."
                )
                continue

            if not all(
                character.isalnum()
                or character in "-_"
                for character in cleaned
            ):
                errors[field_name] = (
                    "Use only letters, numbers, "
                    "hyphens or underscores."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):

        self.invoice_prefix = (
            self.invoice_prefix
            .strip()
            .upper()
        )

        self.receipt_prefix = (
            self.receipt_prefix
            .strip()
            .upper()
        )

        self.expense_prefix = (
            self.expense_prefix
            .strip()
            .upper()
        )

        # Protect the singleton even if somebody bypasses ModelForm.
        if self._state.adding:

            if School.objects.exists():
                raise ValidationError(
                    "Only one school configuration may exist."
                )

        super().save(
            *args,
            **kwargs,
        )

class FeeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Grade(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SchoolClass(models.Model):
    name = models.CharField(max_length=50)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.grade.name} - {self.name}"
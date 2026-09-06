from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping, Any

from django.utils import timezone


# ============================================================
# OVERDUE AGING KEYS
# ============================================================

AGING_1_7 = "1_7"
AGING_8_30 = "8_30"
AGING_31_60 = "31_60"
AGING_60_PLUS = "60_plus"


AGING_LABELS = {
    AGING_1_7: "1–7 Days",
    AGING_8_30: "8–30 Days",
    AGING_31_60: "31–60 Days",
    AGING_60_PLUS: "More Than 60 Days",
}


AGING_ORDER = (
    AGING_1_7,
    AGING_8_30,
    AGING_31_60,
    AGING_60_PLUS,
)


# ============================================================
# RESULT OBJECT
# ============================================================

@dataclass(
    frozen=True,
    slots=True,
)
class OverdueAssessment:
    """
    Pure business result describing whether a financial
    obligation is overdue and, when overdue, its aging bucket.

    This object is intentionally not a Django model.
    Overdue state must be calculated from the source financial
    obligation rather than duplicated into another collection.
    """

    is_overdue: bool
    days_overdue: int
    aging_bucket: str
    aging_label: str


# ============================================================
# DECIMAL NORMALIZATION
# ============================================================

def _to_decimal(value: Any) -> Decimal:
    """
    Safely normalize monetary values to Decimal.

    Invalid or empty values are treated as zero because they
    cannot represent an overdue outstanding balance.
    """

    if value is None:
        return Decimal("0.00")

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(
            str(value)
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return Decimal("0.00")


# ============================================================
# AGING CLASSIFICATION
# ============================================================

def classify_overdue_days(
    days_overdue: int,
) -> tuple[str, str]:
    """
    Return the BRD aging bucket and display label.

    Expected buckets:
        1–7 days
        8–30 days
        31–60 days
        More than 60 days
    """

    if days_overdue <= 0:
        return "", ""

    if days_overdue <= 7:
        key = AGING_1_7

    elif days_overdue <= 30:
        key = AGING_8_30

    elif days_overdue <= 60:
        key = AGING_31_60

    else:
        key = AGING_60_PLUS

    return (
        key,
        AGING_LABELS[key],
    )


# ============================================================
# CORE OVERDUE RULE
# ============================================================

def assess_overdue(
    *,
    due_date: date | None,
    outstanding_amount: Any,
    as_of_date: date | None = None,
) -> OverdueAssessment:
    """
    Evaluate one financial obligation.

    BRD overdue rule:

        Due Date < Current Date
        AND
        Outstanding Amount > 0

    No database state is changed here.
    """

    today = (
        as_of_date
        or timezone.localdate()
    )

    amount = _to_decimal(
        outstanding_amount
    )

    # No due date means the obligation cannot be classified.
    if due_date is None:
        return OverdueAssessment(
            is_overdue=False,
            days_overdue=0,
            aging_bucket="",
            aging_label="",
        )

    # Outstanding balance must be strictly greater than zero.
    if amount <= Decimal("0.00"):
        return OverdueAssessment(
            is_overdue=False,
            days_overdue=0,
            aging_bucket="",
            aging_label="",
        )

    # A payment due today is not past due yet.
    if due_date >= today:
        return OverdueAssessment(
            is_overdue=False,
            days_overdue=0,
            aging_bucket="",
            aging_label="",
        )

    days_overdue = (
        today - due_date
    ).days

    aging_bucket, aging_label = (
        classify_overdue_days(
            days_overdue
        )
    )

    return OverdueAssessment(
        is_overdue=True,
        days_overdue=days_overdue,
        aging_bucket=aging_bucket,
        aging_label=aging_label,
    )


# ============================================================
# SIMPLE BOOLEAN HELPER
# ============================================================

def is_overdue_balance(
    *,
    due_date: date | None,
    outstanding_amount: Any,
    as_of_date: date | None = None,
) -> bool:
    """
    Convenience wrapper used by future invoice/installment
    adapters.
    """

    return assess_overdue(
        due_date=due_date,
        outstanding_amount=outstanding_amount,
        as_of_date=as_of_date,
    ).is_overdue


# ============================================================
# GENERIC ROW BUILDER
# ============================================================

def build_overdue_row(
    *,
    source_id: Any,
    invoice_number: str,
    student_reference: str,
    student_name: str,
    due_date: date,
    outstanding_amount: Any,
    academic_year: str = "",
    grade: str = "",
    class_name: str = "",
    source_status: str = "",
    as_of_date: date | None = None,
) -> dict | None:
    """
    Convert a future real Student Invoice into a standard
    overdue row for the Developer 3 overdue dashboard.

    This function deliberately receives primitive values instead
    of importing Developer 2's Invoice model.

    Once the Invoice model exists, the adapter/view will pass
    its real fields here.
    """

    assessment = assess_overdue(
        due_date=due_date,
        outstanding_amount=outstanding_amount,
        as_of_date=as_of_date,
    )

    if not assessment.is_overdue:
        return None

    amount = _to_decimal(
        outstanding_amount
    )

    return {
        "source_id": str(source_id),
        "invoice_number": (
            invoice_number
            or ""
        ).strip(),
        "student_reference": (
            student_reference
            or ""
        ).strip(),
        "student_name": (
            student_name
            or ""
        ).strip(),
        "academic_year": (
            academic_year
            or ""
        ).strip(),
        "grade": (
            grade
            or ""
        ).strip(),
        "class_name": (
            class_name
            or ""
        ).strip(),
        "due_date": due_date,
        "outstanding_amount": amount,
        "source_status": (
            source_status
            or ""
        ).strip(),
        "days_overdue":
            assessment.days_overdue,
        "aging_bucket":
            assessment.aging_bucket,
        "aging_label":
            assessment.aging_label,
    }


# ============================================================
# METRIC SUMMARY
# ============================================================

def summarize_overdue_rows(
    rows: Iterable[Mapping[str, Any]],
) -> dict:
    """
    Build reusable overdue KPI totals.

    The same summary can later be consumed by:
        - overdue_list.html
        - dashboard.html
        - Overdue Payment Report

    Student count is deduplicated by student_reference.
    """

    normalized_rows = list(
        rows
    )

    total_amount = Decimal(
        "0.00"
    )

    bucket_amounts = {
        key: Decimal("0.00")
        for key in AGING_ORDER
    }

    bucket_counts = {
        key: 0
        for key in AGING_ORDER
    }

    student_keys = set()

    for row in normalized_rows:

        amount = _to_decimal(
            row.get(
                "outstanding_amount"
            )
        )

        total_amount += amount

        bucket = (
            row.get(
                "aging_bucket"
            )
            or ""
        )

        if bucket in bucket_amounts:

            bucket_amounts[
                bucket
            ] += amount

            bucket_counts[
                bucket
            ] += 1

        student_reference = (
            row.get(
                "student_reference"
            )
            or ""
        ).strip()

        student_name = (
            row.get(
                "student_name"
            )
            or ""
        ).strip()

        student_key = (
            student_reference
            or student_name
        )

        if student_key:
            student_keys.add(
                student_key
            )

    return {
        "overdue_invoice_count":
            len(normalized_rows),

        "overdue_student_count":
            len(student_keys),

        "total_overdue_amount":
            total_amount,

        "aging_1_7_count":
            bucket_counts[
                AGING_1_7
            ],

        "aging_1_7_amount":
            bucket_amounts[
                AGING_1_7
            ],

        "aging_8_30_count":
            bucket_counts[
                AGING_8_30
            ],

        "aging_8_30_amount":
            bucket_amounts[
                AGING_8_30
            ],

        "aging_31_60_count":
            bucket_counts[
                AGING_31_60
            ],

        "aging_31_60_amount":
            bucket_amounts[
                AGING_31_60
            ],

        "aging_60_plus_count":
            bucket_counts[
                AGING_60_PLUS
            ],

        "aging_60_plus_amount":
            bucket_amounts[
                AGING_60_PLUS
            ],
    }
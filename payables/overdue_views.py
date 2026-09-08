from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from school_config.models import School

from .views import get_school_currency

from .overdue_services import (
    AGING_1_7,
    AGING_8_30,
    AGING_31_60,
    AGING_60_PLUS,
    summarize_overdue_rows,
)



# ============================================================
# SCHOOL CURRENCY
# ============================================================

def get_school_currency():
    """
    Return the configured school currency.

    Uses the same behavior as the existing payables views:
    School.default_currency when configured, otherwise USD.
    """

    school = (
        School.objects
        .first()
    )

    if (
        school
        and school.default_currency
    ):
        return school.default_currency

    return "USD"



# ============================================================
# OVERDUE SOURCE ADAPTER
# ============================================================

# Keep the existing import location compatible with callers.
from .student_finance_services import get_student_invoice_overdue_rows


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalized_text(value):
    return str(
        value or ""
    ).strip().lower()


def _row_matches_search(
    row,
    search,
):
    if not search:
        return True

    haystack = " ".join(
        [
            str(
                row.get(
                    "invoice_number",
                    "",
                )
            ),
            str(
                row.get(
                    "student_reference",
                    "",
                )
            ),
            str(
                row.get(
                    "student_name",
                    "",
                )
            ),
            str(
                row.get(
                    "academic_year",
                    "",
                )
            ),
            str(
                row.get(
                    "grade",
                    "",
                )
            ),
            str(
                row.get(
                    "class_name",
                    "",
                )
            ),
        ]
    ).lower()

    return search in haystack


# ============================================================
# SORTING
# ============================================================

SORT_OPTIONS = {
    "days_desc":
        "Most Overdue",

    "days_asc":
        "Least Overdue",

    "amount_desc":
        "Highest Outstanding",

    "amount_asc":
        "Lowest Outstanding",

    "due_date_asc":
        "Oldest Due Date",

    "due_date_desc":
        "Newest Due Date",

    "student_asc":
        "Student A–Z",
}


def _sort_overdue_rows(
    rows,
    sort_key,
):
    if sort_key == "days_asc":

        return sorted(
            rows,
            key=lambda row:
                row.get(
                    "days_overdue",
                    0,
                ),
        )

    if sort_key == "amount_desc":

        return sorted(
            rows,
            key=lambda row:
                row.get(
                    "outstanding_amount",
                    Decimal("0.00"),
                ),
            reverse=True,
        )

    if sort_key == "amount_asc":

        return sorted(
            rows,
            key=lambda row:
                row.get(
                    "outstanding_amount",
                    Decimal("0.00"),
                ),
        )

    if sort_key == "due_date_asc":

        return sorted(
            rows,
            key=lambda row:
                row.get(
                    "due_date"
                ),
        )

    if sort_key == "due_date_desc":

        return sorted(
            rows,
            key=lambda row:
                row.get(
                    "due_date"
                ),
            reverse=True,
        )

    if sort_key == "student_asc":

        return sorted(
            rows,
            key=lambda row:
                _normalized_text(
                    row.get(
                        "student_name"
                    )
                    or
                    row.get(
                        "student_reference"
                    )
                ),
        )

    # Default:
    # Critical / longest overdue first.
    return sorted(
        rows,
        key=lambda row:
            row.get(
                "days_overdue",
                0,
            ),
        reverse=True,
    )


# ============================================================
# OVERDUE LIST
# ============================================================

@login_required
def overdue_list(
    request,
):
    """
    Developer 3 Overdue Tracking command center.

    Overdue rows are derived from student invoices.
    No separate overdue financial collection is created.
    """

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
        .lower()
    )

    aging = (
        request.GET.get(
            "aging",
            ""
        )
        .strip()
    )

    sort = (
        request.GET.get(
            "sort",
            "days_desc"
        )
        .strip()
    )

    valid_aging = {
        "",
        AGING_1_7,
        AGING_8_30,
        AGING_31_60,
        AGING_60_PLUS,
    }

    if aging not in valid_aging:
        aging = ""

    if sort not in SORT_OPTIONS:
        sort = "days_desc"

    # --------------------------------------------------------
    # SOURCE DATA
    # --------------------------------------------------------

    all_rows = list(
        get_student_invoice_overdue_rows()
    )

    # --------------------------------------------------------
    # COMPLETE REGISTER KPIs
    #
    # KPI cards intentionally summarize all overdue records,
    # not only the filtered table.
    # --------------------------------------------------------

    summary = summarize_overdue_rows(
        all_rows
    )

    # --------------------------------------------------------
    # FILTERING
    # --------------------------------------------------------

    filtered_rows = []

    for row in all_rows:

        if not _row_matches_search(
            row,
            search,
        ):
            continue

        if (
            aging
            and
            row.get(
                "aging_bucket"
            )
            != aging
        ):
            continue

        filtered_rows.append(
            row
        )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    filtered_rows = (
        _sort_overdue_rows(
            filtered_rows,
            sort,
        )
    )

    # --------------------------------------------------------
    # FILTERED TOTAL
    # --------------------------------------------------------

    filtered_amount = sum(
        (
            row.get(
                "outstanding_amount",
                Decimal("0.00"),
            )
            for row in filtered_rows
        ),
        Decimal("0.00"),
    )

    # --------------------------------------------------------
    # SOURCE INTEGRATION STATE
    #
    # The adapter reads issued billing.Invoice records.
    # --------------------------------------------------------

    invoice_integration_ready = True

    context = {
        "overdue_rows":
            filtered_rows,

        "search":
            search,

        "aging":
            aging,

        "sort":
            sort,

        "sort_options":
            SORT_OPTIONS.items(),

        "aging_options": [
            (
                AGING_1_7,
                "1–7 Days",
            ),
            (
                AGING_8_30,
                "8–30 Days",
            ),
            (
                AGING_31_60,
                "31–60 Days",
            ),
            (
                AGING_60_PLUS,
                "More Than 60 Days",
            ),
        ],

        "filtered_count":
            len(
                filtered_rows
            ),

        "filtered_amount":
            filtered_amount,

        "invoice_integration_ready":
            invoice_integration_ready,

        "currency_code":
            get_school_currency(),

        **summary,
    }

    return render(
        request,
        "payables/overdue_list.html",
        context,
    )




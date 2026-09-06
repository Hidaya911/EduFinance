from bson.objectid import ObjectId

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from pymongo import MongoClient

from .forms import AcademicYearForm
from .models import AcademicYear


ADMIN_ROLE_NAMES = {
    "super admin",
    "super administrator",
    "school administrator",
}


# ============================================================
# ACCESS CONTROL
# ============================================================

def is_admin(user):
    """
    Allow only Super Admins and School Administrators
    into configuration.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    allowed_roles = {
        "Super Admin",
        "Super Administrator",
        "School Administrator",
    }

    if user.groups.filter(
        name__in=allowed_roles
    ).exists():
        return True

    # --------------------------------------------------------
    # Support users whose group link was saved directly
    # in MongoDB.
    # --------------------------------------------------------

    try:
        client = MongoClient(
            settings.MONGO_URI
        )

        db = client[
            settings.DATABASES[
                "default"
            ]["NAME"]
        ]

        user_ids = [
            user.pk,
            str(user.pk),
        ]

        if ObjectId.is_valid(
            str(user.pk)
        ):
            user_ids.append(
                ObjectId(
                    str(user.pk)
                )
            )

        user_doc = (
            db["auth_user"]
            .find_one(
                {
                    "$or": [
                        {
                            "id": {
                                "$in":
                                    user_ids
                            }
                        },
                        {
                            "_id": {
                                "$in":
                                    user_ids
                            }
                        },
                    ]
                }
            )
        )

        if user_doc:
            user_ids.extend(
                [
                    user_doc.get("id"),
                    user_doc.get("_id"),
                ]
            )

        valid_user_ids = [
            value
            for value
            in user_ids
            if value is not None
        ]

        group_ids = [
            link.get("group_id")
            for link
            in db[
                "auth_user_groups"
            ].find(
                {
                    "user_id": {
                        "$in":
                            valid_user_ids
                    }
                }
            )
        ]

        return (
            db["auth_group"]
            .count_documents(
                {
                    "$and": [
                        {
                            "$or": [
                                {
                                    "id": {
                                        "$in":
                                            group_ids
                                    }
                                },
                                {
                                    "_id": {
                                        "$in":
                                            group_ids
                                    }
                                },
                            ]
                        },
                        {
                            "name": {
                                "$in":
                                    list(
                                        allowed_roles
                                    )
                            }
                        },
                    ]
                }
            )
            > 0
        )

    except Exception:
        return False


# ============================================================
# ACADEMIC YEAR LIST
# ============================================================

@login_required
@user_passes_test(is_admin)
def academic_years_list(request):
    today = timezone.localdate()

    years = (
        AcademicYear
        .objects
        .all()
        .order_by(
            "-start_date"
        )
    )

    total_years = (
        years.count()
    )

    current_year = (
        AcademicYear
        .objects
        .filter(
            is_current=True
        )
        .order_by(
            "-start_date"
        )
        .first()
    )

    historical_count = (
        AcademicYear
        .objects
        .filter(
            end_date__lt=today,
            is_current=False,
        )
        .count()
    )

    upcoming_count = (
        AcademicYear
        .objects
        .filter(
            start_date__gt=today,
            is_current=False,
        )
        .count()
    )

    active_window_count = (
        AcademicYear
        .objects
        .filter(
            start_date__lte=today,
            end_date__gte=today,
            is_current=False,
        )
        .count()
    )

    context = {
        "years":
            years,

        "today":
            today,

        "total_years":
            total_years,

        "current_year":
            current_year,

        "historical_count":
            historical_count,

        "upcoming_count":
            upcoming_count,

        "active_window_count":
            active_window_count,
    }

    return render(
        request,
        "core/academic_years_list.html",
        context,
    )


# ============================================================
# CREATE / EDIT ACADEMIC YEAR
# ============================================================

@login_required
@user_passes_test(is_admin)
def academic_year_form_view(
    request,
    pk=None,
):
    year = (
        get_object_or_404(
            AcademicYear,
            pk=pk,
        )
        if pk
        else None
    )

    current_year = (
        AcademicYear
        .objects
        .filter(
            is_current=True
        )
        .order_by(
            "-start_date"
        )
        .first()
    )

    if request.method == "POST":

        form = AcademicYearForm(
            request.POST,
            instance=year,
        )

        if form.is_valid():

            saved_year = (
                form.save()
            )

            # ------------------------------------------------
            # Only one academic year can be current.
            # ------------------------------------------------

            if saved_year.is_current:

                (
                    AcademicYear
                    .objects
                    .exclude(
                        pk=saved_year.pk
                    )
                    .filter(
                        is_current=True
                    )
                    .update(
                        is_current=False
                    )
                )

            if pk:

                messages.success(
                    request,
                    (
                        f"Academic year "
                        f"'{saved_year.name}' "
                        f"was updated successfully."
                    ),
                )

            else:

                messages.success(
                    request,
                    (
                        f"Academic year "
                        f"'{saved_year.name}' "
                        f"was created successfully."
                    ),
                )

            return redirect(
                "academic_years_list"
            )

    else:

        form = AcademicYearForm(
            instance=year
        )

    context = {
        "form":
            form,

        "is_edit":
            bool(pk),

        "year":
            year,

        "current_year":
            current_year,
    }

    return render(
        request,
        "core/academic_year_form.html",
        context,
    )
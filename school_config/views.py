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
from django.views.decorators.http import require_POST

from .forms import (
    FeeCategoryForm,
    GradeForm,
    SchoolClassForm,
    SchoolForm,
)
from .models import (
    FeeCategory,
    Grade,
    School,
    SchoolClass,
)


# ============================================================
# PERMISSION HELPERS
# ============================================================


def is_super_admin(user):
    """
    Fee categories are reserved for Super Administrator users.
    """

    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(
                name__in=[
                    "Super Admin",
                    "Super Administrator",
                ]
            ).exists()
        )
    )


def can_manage_academics(user):
    """
    Academic configuration can be managed by Super Admin
    and School Administrator roles.
    """

    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(
                name__in=[
                    "Super Admin",
                    "Super Administrator",
                    "School Administrator",
                    "School Admin",
                ]
            ).exists()
            or getattr(
                user,
                "role",
                None,
            )
            in [
                "Super Administrator",
                "School Administrator",
                "Super Admin",
                "School Admin",
            ]
        )
    )


# ============================================================
# SCHOOL SETTINGS
# ============================================================


@login_required
def school_settings(request):
    school = (
        School.objects
        .first()
    )

    if request.method == "POST":
        form = SchoolForm(
            request.POST,
            request.FILES,
            instance=school,
        )

        if form.is_valid():
            school = form.save()

            messages.success(
                request,
                (
                    "School configuration "
                    "was saved successfully."
                ),
            )

            return redirect(
                "school_config:school_settings"
            )

    else:
        form = SchoolForm(
            instance=school,
        )

    return render(
        request,
        "school_config/school_settings.html",
        {
            "form": form,
            "school": school,
            "is_configured": (
                school is not None
            ),
        },
    )


# ============================================================
# FEE CATEGORIES
# ============================================================


@login_required
@user_passes_test(is_super_admin)
def fee_categories_list_view(request):
    categories = (
        FeeCategory.objects
        .all()
        .order_by("name")
    )

    return render(
        request,
        "school_config/fee_categories_list.html",
        {
            "categories": categories,
        },
    )


@login_required
@user_passes_test(is_super_admin)
def fee_category_create_view(request):
    if request.method == "POST":
        form = FeeCategoryForm(
            request.POST
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                (
                    f"Fee category "
                    f"'{category.name}' "
                    "created successfully."
                ),
            )

            return redirect(
                "school_config:fee_categories_list"
            )

    else:
        form = FeeCategoryForm()

    return render(
        request,
        "school_config/fee_category_form.html",
        {
            "form": form,
            "action": "Create",
        },
    )


@login_required
@user_passes_test(is_super_admin)
def fee_category_edit_view(
    request,
    pk,
):
    category = get_object_or_404(
        FeeCategory,
        pk=pk,
    )

    if request.method == "POST":
        form = FeeCategoryForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                (
                    f"Fee category "
                    f"'{category.name}' "
                    "updated successfully."
                ),
            )

            return redirect(
                "school_config:fee_categories_list"
            )

    else:
        form = FeeCategoryForm(
            instance=category
        )

    return render(
        request,
        "school_config/fee_category_form.html",
        {
            "form": form,
            "action": "Edit",
        },
    )


@login_required
@user_passes_test(is_super_admin)
def fee_category_toggle_status_view(
    request,
    pk,
):
    category = get_object_or_404(
        FeeCategory,
        pk=pk,
    )

    category.is_active = (
        not category.is_active
    )

    category.save()

    status_text = (
        "activated"
        if category.is_active
        else "deactivated"
    )

    messages.success(
        request,
        (
            f"Fee category "
            f"'{category.name}' "
            f"has been {status_text}."
        ),
    )

    return redirect(
        "school_config:fee_categories_list"
    )


@login_required
@user_passes_test(is_super_admin)
def fee_category_delete_view(
    request,
    pk,
):
    category = get_object_or_404(
        FeeCategory,
        pk=pk,
    )

    category_name = (
        category.name
    )

    category.delete()

    messages.success(
        request,
        (
            f"Fee category "
            f"'{category_name}' "
            "was deleted successfully."
        ),
    )

    return redirect(
        "school_config:fee_categories_list"
    )


# ============================================================
# GRADES
# ============================================================


@login_required
@user_passes_test(can_manage_academics)
def grades_list_view(request):
    grades = list(
        Grade.objects
        .prefetch_related("classes")
        .order_by("name")
    )

    grade_rows = []

    total_classes = 0
    active_classes = 0
    grades_with_sections = 0

    for grade in grades:
        classes = list(
            grade.classes.all()
        )

        class_count = len(
            classes
        )

        active_class_count = sum(
            1
            for school_class in classes
            if school_class.is_active
        )

        inactive_class_count = (
            class_count
            - active_class_count
        )

        if class_count > 0:
            grades_with_sections += 1

        total_classes += (
            class_count
        )

        active_classes += (
            active_class_count
        )

        grade_rows.append(
            {
                "grade":
                    grade,

                "classes":
                    classes,

                "class_count":
                    class_count,

                "active_class_count":
                    active_class_count,

                "inactive_class_count":
                    inactive_class_count,
            }
        )

    grade_count = len(
        grades
    )

    school = (
        School.objects
        .first()
    )

    if (
        school
        and school.current_academic_year
        and school.current_academic_year.strip()
    ):
        current_academic_year = (
            school.current_academic_year
            .strip()
        )
    else:
        current_academic_year = (
            "Not configured"
        )

    return render(
        request,
        "school_config/grades_list.html",
        {
            "grade_rows":
                grade_rows,

            "grade_count":
                grade_count,

            "total_classes":
                total_classes,

            "active_classes":
                active_classes,

            "grades_with_sections":
                grades_with_sections,

            "grades_without_sections":
                (
                    grade_count
                    - grades_with_sections
                ),

            "current_academic_year":
                current_academic_year,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
def grade_create_view(request):
    if request.method == "POST":
        form = GradeForm(
            request.POST
        )

        if form.is_valid():
            grade = form.save()

            messages.success(
                request,
                (
                    f"Grade "
                    f"'{grade.name}' "
                    "created successfully."
                ),
            )

            return redirect(
                "school_config:grades_list"
            )

    else:
        form = GradeForm()

    return render(
        request,
        "school_config/grade_form.html",
        {
            "form":
                form,

            "action":
                "Create",

            "is_edit":
                False,

            "grade":
                None,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
def grade_edit_view(
    request,
    pk,
):
    grade = get_object_or_404(
        Grade,
        pk=pk,
    )

    if request.method == "POST":
        form = GradeForm(
            request.POST,
            instance=grade,
        )

        if form.is_valid():
            grade = form.save()

            messages.success(
                request,
                (
                    f"Grade "
                    f"'{grade.name}' "
                    "updated successfully."
                ),
            )

            return redirect(
                "school_config:grades_list"
            )

    else:
        form = GradeForm(
            instance=grade
        )

    return render(
        request,
        "school_config/grade_form.html",
        {
            "form":
                form,

            "action":
                "Edit",

            "is_edit":
                True,

            "grade":
                grade,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
@require_POST
def grade_delete_view(
    request,
    pk,
):
    grade = get_object_or_404(
        Grade,
        pk=pk,
    )

    grade_name = (
        grade.name
    )

    class_count = (
        grade.classes.count()
    )

    grade.delete()

    if class_count > 0:
        messages.success(
            request,
            (
                f"Grade "
                f"'{grade_name}' "
                "and its associated "
                f"{class_count} "
                "class/section record(s) "
                "were removed."
            ),
        )

    else:
        messages.success(
            request,
            (
                f"Grade "
                f"'{grade_name}' "
                "deleted successfully."
            ),
        )

    return redirect(
        "school_config:grades_list"
    )


# ============================================================
# CLASSES / SECTIONS
# ============================================================


@login_required
@user_passes_test(can_manage_academics)
def classes_list_view(request):
    classes = list(
        SchoolClass.objects
        .select_related("grade")
        .order_by(
            "grade__name",
            "name",
        )
    )

    grades = list(
        Grade.objects
        .all()
        .order_by("name")
    )

    # ========================================================
    # COUNTS
    # ========================================================

    total_classes = len(
        classes
    )

    active_classes = sum(
        1
        for school_class in classes
        if school_class.is_active
    )

    inactive_classes = (
        total_classes
        - active_classes
    )

    # ========================================================
    # GRADE DISTRIBUTION
    # ========================================================

    class_counts_by_grade = {}
    active_counts_by_grade = {}

    for school_class in classes:
        grade_key = str(
            school_class.grade.pk
        )

        class_counts_by_grade[
            grade_key
        ] = (
            class_counts_by_grade.get(
                grade_key,
                0,
            )
            + 1
        )

        if school_class.is_active:
            active_counts_by_grade[
                grade_key
            ] = (
                active_counts_by_grade.get(
                    grade_key,
                    0,
                )
                + 1
            )

    max_grade_class_count = max(
        class_counts_by_grade.values(),
        default=0,
    )

    grade_distribution = []

    grades_covered = 0
    grades_without_sections = 0
    multi_section_grades = 0

    for grade in grades:
        grade_key = str(
            grade.pk
        )

        class_count = (
            class_counts_by_grade.get(
                grade_key,
                0,
            )
        )

        active_count = (
            active_counts_by_grade.get(
                grade_key,
                0,
            )
        )

        inactive_count = (
            class_count
            - active_count
        )

        if class_count > 0:
            grades_covered += 1
        else:
            grades_without_sections += 1

        if class_count > 1:
            multi_section_grades += 1

        if (
            max_grade_class_count
            > 0
        ):
            bar_percent = round(
                (
                    class_count
                    / max_grade_class_count
                )
                * 100
            )
        else:
            bar_percent = 0

        grade_distribution.append(
            {
                "grade":
                    grade,

                "class_count":
                    class_count,

                "active_count":
                    active_count,

                "inactive_count":
                    inactive_count,

                "bar_percent":
                    bar_percent,
            }
        )

    # ========================================================
    # ACADEMIC YEAR
    # ========================================================

    school = (
        School.objects
        .first()
    )

    if (
        school
        and school.current_academic_year
        and school.current_academic_year.strip()
    ):
        current_academic_year = (
            school.current_academic_year
            .strip()
        )
    else:
        current_academic_year = (
            "Not configured"
        )

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "school_config/classes_list.html",
        {
            "classes":
                classes,

            "grades":
                grades,

            "total_classes":
                total_classes,

            "active_classes":
                active_classes,

            "inactive_classes":
                inactive_classes,

            "grades_covered":
                grades_covered,

            "grades_without_sections":
                grades_without_sections,

            "multi_section_grades":
                multi_section_grades,

            "grade_distribution":
                grade_distribution,

            "current_academic_year":
                current_academic_year,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
def class_create_view(request):
    if request.method == "POST":
        form = SchoolClassForm(
            request.POST
        )

        if form.is_valid():
            school_class = (
                form.save()
            )

            messages.success(
                request,
                (
                    f"Class section "
                    f"'{school_class}' "
                    "created successfully."
                ),
            )

            return redirect(
                "school_config:classes_list"
            )

    else:
        form = SchoolClassForm()

    return render(
        request,
        "school_config/class_form.html",
        {
            "form":
                form,

            "action":
                "Create",

            "is_edit":
                False,

            "school_class":
                None,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
def class_edit_view(
    request,
    pk,
):
    school_class = get_object_or_404(
        SchoolClass,
        pk=pk,
    )

    if request.method == "POST":
        form = SchoolClassForm(
            request.POST,
            instance=school_class,
        )

        if form.is_valid():
            school_class = (
                form.save()
            )

            messages.success(
                request,
                (
                    f"Class section "
                    f"'{school_class}' "
                    "updated successfully."
                ),
            )

            return redirect(
                "school_config:classes_list"
            )

    else:
        form = SchoolClassForm(
            instance=school_class
        )

    return render(
        request,
        "school_config/class_form.html",
        {
            "form":
                form,

            "action":
                "Edit",

            "is_edit":
                True,

            "school_class":
                school_class,
        },
    )


@login_required
@user_passes_test(can_manage_academics)
@require_POST
def class_delete_view(
    request,
    pk,
):
    school_class = get_object_or_404(
        SchoolClass,
        pk=pk,
    )

    class_name = str(
        school_class
    )

    school_class.delete()

    messages.success(
        request,
        (
            f"Class section "
            f"'{class_name}' "
            "deleted successfully."
        ),
    )

    return redirect(
        "school_config:classes_list"
    )
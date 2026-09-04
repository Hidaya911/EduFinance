from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from .models import Student, Enrollment, Guardian, StudentGuardian
from .forms import StudentForm, GuardianForm

from .permissions import (
    roles_required,
    user_has_role,
    ROLE_SUPER_ADMIN,
    ROLE_SCHOOL_ADMIN,
    ROLE_ACCOUNTANT,
    ROLE_CASHIER,
    ROLE_AUDITOR,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def generate_student_number():
    last_student = Student.objects.order_by(
        "-student_number"
    ).first()

    if last_student and last_student.student_number:
        try:
            last_number = int(
                last_student.student_number.split("-")[1]
            )
            next_number = last_number + 1

        except (IndexError, ValueError):
            next_number = 1

    else:
        next_number = 1

    return f"STU-{next_number:06d}"


def get_student(student_id):
    return get_object_or_404(
        Student,
        pk=student_id,
    )


def can_manage_students(user):
    """
    Student CRUD:
    Accountant + Super Administrator.
    """

    return user_has_role(
        user,
        [
            ROLE_ACCOUNTANT,
            ROLE_SUPER_ADMIN,
        ],
    )


# --------------------------------------------------
# Student List
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SCHOOL_ADMIN,
    ROLE_SUPER_ADMIN,
)
def student_list(request):
    students = Student.objects.all().order_by(
        "first_name",
        "last_name",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        students = students.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(student_number__icontains=search)
            | Q(admission_number__icontains=search)
        )

    if status:
        students = students.filter(
            status=status
        )

    context = {
        "students": students,
        "search": search,
        "selected_status": status,
        "can_manage_students": can_manage_students(
            request.user
        ),
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(
            request,
            "students/partials/student_results.html",
            context,
        )

    return render(
        request,
        "students/student_list.html",
        context,
    )


# --------------------------------------------------
# Create Student
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def student_create(request):
    if request.method == "POST":
        form = StudentForm(
            request.POST
        )

        if form.is_valid():
            student = form.save(
                commit=False
            )

            student.student_number = (
                generate_student_number()
            )

            student.save()

            enrollment_date = (
                form.cleaned_data.get(
                    "enrollment_date"
                )
            )

            if enrollment_date:
                Enrollment.objects.create(
                    student_id=str(
                        student.pk
                    ),
                    enrollment_date=enrollment_date,
                    status="active",
                )

            messages.success(
                request,
                "Student created successfully.",
            )

            return redirect(
                "students:student_financial_profile",
                student_id=str(
                    student.pk
                ),
            )

    else:
        form = StudentForm()

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "page_title": "Add Student",
            "button_text": "Create Student",
            "is_edit": False,
        },
    )


# --------------------------------------------------
# Edit Student
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def student_edit(
    request,
    student_id,
):
    student = get_student(
        student_id
    )

    enrollment = (
        Enrollment.objects.filter(
            student_id=str(
                student.pk
            ),
            status="active",
        ).first()
    )

    initial = {}

    if enrollment:
        initial["enrollment_date"] = (
            enrollment.enrollment_date
        )

    if request.method == "POST":
        form = StudentForm(
            request.POST,
            instance=student,
        )

        if form.is_valid():
            student = form.save()

            enrollment_date = (
                form.cleaned_data.get(
                    "enrollment_date"
                )
            )

            if enrollment:
                if enrollment_date:
                    enrollment.enrollment_date = (
                        enrollment_date
                    )
                    enrollment.save()

            elif enrollment_date:
                Enrollment.objects.create(
                    student_id=str(
                        student.pk
                    ),
                    enrollment_date=enrollment_date,
                    status="active",
                )

            messages.success(
                request,
                "Student updated successfully.",
            )

            return redirect(
                "students:student_financial_profile",
                student_id=str(
                    student.pk
                ),
            )

    else:
        form = StudentForm(
            instance=student,
            initial=initial,
        )

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "student": student,
            "page_title": "Edit Student",
            "button_text": "Save Changes",
            "is_edit": True,
        },
    )


# --------------------------------------------------
# Deactivate Student
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def student_delete(
    request,
    student_id,
):
    student = get_student(
        student_id
    )

    if request.method != "POST":
        raise Http404()

    if student.status == "inactive":
        messages.info(
            request,
            "Student is already inactive.",
        )

        return redirect(
            "students:student_list"
        )

    student.status = "inactive"
    student.save()

    messages.success(
        request,
        f"{student.full_name} was deactivated successfully.",
    )

    return redirect(
        "students:student_list"
    )


# --------------------------------------------------
# Student Financial Profile
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_CASHIER,
    ROLE_SCHOOL_ADMIN,
    ROLE_AUDITOR,
    ROLE_SUPER_ADMIN,
)
def student_financial_profile(
    request,
    student_id,
):
    student = get_student(
        student_id
    )

    enrollment = (
        Enrollment.objects.filter(
            student_id=str(
                student.pk
            ),
            status="active",
        ).first()
    )

    financial_summary = {
        "total_invoiced": 0,
        "total_discounts": 0,
        "total_scholarships": 0,
        "total_paid": 0,
        "total_refunded": 0,
        "outstanding_balance": 0,
        "overdue_amount": 0,
        "upcoming_installments": 0,
    }

    context = {
        "student": student,
        "enrollment": enrollment,
        "financial_summary": financial_summary,
        "can_manage_students": (
            can_manage_students(
                request.user
            )
        ),
    }

    return render(
        request,
        "students/student_financial_profile.html",
        context,
    )


# --------------------------------------------------
# Guardian Helpers
# --------------------------------------------------

def get_guardian(guardian_id):
    return get_object_or_404(
        Guardian,
        pk=guardian_id,
    )


def get_guardian_student_ids(guardian):
    return list(
        StudentGuardian.objects.filter(
            guardian_id=str(
                guardian.pk
            )
        ).values_list(
            "student_id",
            flat=True,
        )
    )


# --------------------------------------------------
# Guardian List
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def guardian_list(request):
    guardians = Guardian.objects.all().order_by(
        "first_name",
        "last_name",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        guardians = guardians.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
        )

    if status:
        guardians = guardians.filter(
            status=status
        )

    guardian_rows = []

    for guardian in guardians:
        student_ids = get_guardian_student_ids(
            guardian
        )

        linked_students = Student.objects.filter(
            pk__in=student_ids
        )

        guardian_rows.append(
            {
                "guardian": guardian,
                "students": linked_students,
            }
        )

    context = {
        "guardian_rows": guardian_rows,
        "search": search,
        "selected_status": status,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(
            request,
            "students/partials/guardian_results.html",
            context,
        )

    return render(
        request,
        "students/guardian_list.html",
        context,
    )


# --------------------------------------------------
# Guardian Create
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def guardian_create(request):
    if request.method == "POST":
        form = GuardianForm(
            request.POST
        )

        if form.is_valid():
            guardian = form.save()

            selected_students = (
                form.cleaned_data[
                    "students"
                ]
            )

            primary_student = (
                form.cleaned_data.get(
                    "primary_student"
                )
            )

            for student in selected_students:
                StudentGuardian.objects.create(
                    student_id=str(
                        student.pk
                    ),
                    guardian_id=str(
                        guardian.pk
                    ),
                    is_primary=(
                        primary_student is not None
                        and student.pk
                        == primary_student.pk
                    ),
                )

            messages.success(
                request,
                "Guardian created successfully.",
            )

            return redirect(
                "students:guardian_list"
            )

    else:
        form = GuardianForm()

    return render(
        request,
        "students/guardian_form.html",
        {
            "form": form,
            "page_title": "Add Guardian",
            "button_text": "Create Guardian",
        },
    )


# --------------------------------------------------
# Guardian Edit
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def guardian_edit(
    request,
    guardian_id,
):
    guardian = get_guardian(
        guardian_id
    )

    links = StudentGuardian.objects.filter(
        guardian_id=str(
            guardian.pk
        )
    )

    linked_student_ids = [
        link.student_id
        for link in links
    ]

    primary_link = links.filter(
        is_primary=True
    ).first()

    primary_student = None

    if primary_link:
        primary_student = Student.objects.filter(
            pk=primary_link.student_id
        ).first()

    initial = {
        "students": linked_student_ids,
        "primary_student": primary_student,
    }

    if request.method == "POST":
        form = GuardianForm(
            request.POST,
            instance=guardian,
        )

        if form.is_valid():
            guardian = form.save()

            selected_students = list(
                form.cleaned_data[
                    "students"
                ]
            )

            primary_student = (
                form.cleaned_data.get(
                    "primary_student"
                )
            )

            StudentGuardian.objects.filter(
                guardian_id=str(
                    guardian.pk
                )
            ).delete()

            for student in selected_students:
                StudentGuardian.objects.create(
                    student_id=str(
                        student.pk
                    ),
                    guardian_id=str(
                        guardian.pk
                    ),
                    is_primary=(
                        primary_student is not None
                        and student.pk
                        == primary_student.pk
                    ),
                )

            messages.success(
                request,
                "Guardian updated successfully.",
            )

            return redirect(
                "students:guardian_list"
            )

    else:
        form = GuardianForm(
            instance=guardian,
            initial=initial,
        )

    return render(
        request,
        "students/guardian_form.html",
        {
            "form": form,
            "guardian": guardian,
            "page_title": "Edit Guardian",
            "button_text": "Save Changes",
        },
    )


# --------------------------------------------------
# Guardian Deactivate
# --------------------------------------------------

@roles_required(
    ROLE_ACCOUNTANT,
    ROLE_SUPER_ADMIN,
)
def guardian_delete(
    request,
    guardian_id,
):
    guardian = get_guardian(
        guardian_id
    )

    if request.method != "POST":
        raise Http404()

    if guardian.status == "inactive":
        messages.info(
            request,
            "Guardian is already inactive.",
        )

        return redirect(
            "students:guardian_list"
        )

    guardian.status = "inactive"
    guardian.save()

    messages.success(
        request,
        f"{guardian.full_name} was deactivated successfully.",
    )

    return redirect(
        "students:guardian_list"
    )

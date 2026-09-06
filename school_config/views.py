from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SchoolForm
from .models import School
from .models import FeeCategory
from .forms import FeeCategoryForm
from .models import Grade, SchoolClass
from .forms import GradeForm, SchoolClassForm

def is_super_admin(user):
    """Fee categories are reserved for Super Admin accounts."""
    return user.is_authenticated and (
        user.is_superuser or
        user.groups.filter(name__in=['Super Admin', 'Super Administrator']).exists()
    )

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
        (
            "school_config/"
            "school_settings.html"
        ),
        {
            "form":
                form,

            "school":
                school,

            "is_configured":
                school is not None,
        },
    )


@login_required
@user_passes_test(is_super_admin)
def fee_categories_list_view(request):
    categories = FeeCategory.objects.all().order_by('name')
    return render(request, 'school_config/fee_categories_list.html', {'categories': categories})

@login_required
@user_passes_test(is_super_admin)
def fee_category_create_view(request):
    if request.method == 'POST':
        form = FeeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee category created successfully.")
            return redirect('school_config:fee_categories_list')
    else:
        form = FeeCategoryForm()
    return render(request, 'school_config/fee_category_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_super_admin)
def fee_category_edit_view(request, pk):
    category = get_object_or_404(FeeCategory, pk=pk)
    if request.method == 'POST':
        form = FeeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee category updated successfully.")
            return redirect('school_config:fee_categories_list')
    else:
        form = FeeCategoryForm(instance=category)
    return render(request, 'school_config/fee_category_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_super_admin)
def fee_category_toggle_status_view(request, pk):
    category = get_object_or_404(FeeCategory, pk=pk)
    category.is_active = not category.is_active
    category.save()
    status_text = "activated" if category.is_active else "deactivated"
    messages.success(request, f"Fee category '{category.name}' has been {status_text}.")
    return redirect('school_config:fee_categories_list')

@login_required
@user_passes_test(is_super_admin)
def fee_category_delete_view(request, pk):
    category = get_object_or_404(FeeCategory, pk=pk)
    category_name = category.name
    category.delete()
    messages.success(request, f"Fee category '{category_name}' was deleted successfully.")
    return redirect('school_config:fee_categories_list')


def can_manage_academics(user):
    """Accessible by Super Administrator and School Administrator roles."""
    return user.is_authenticated and (
        user.is_superuser or
        user.groups.filter(name__in=['Super Admin', 'Super Administrator', 'School Administrator', 'School Admin']).exists() or
        getattr(user, 'role', None) in ['Super Administrator', 'School Administrator', 'Super Admin', 'School Admin']
    )

# --- Grade Views ---
@login_required
@user_passes_test(can_manage_academics)
def grades_list_view(request):
    grades = Grade.objects.all().order_by('name')
    return render(request, 'school_config/grades_list.html', {'grades': grades})

@login_required
@user_passes_test(can_manage_academics)
def grade_create_view(request):
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade created successfully.")
            return redirect('school_config:grades_list')
    else:
        form = GradeForm()
    return render(request, 'school_config/grade_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(can_manage_academics)
def grade_edit_view(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade updated successfully.")
            return redirect('school_config:grades_list')
    else:
        form = GradeForm(instance=grade)
    return render(request, 'school_config/grade_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(can_manage_academics)
def grade_delete_view(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    grade_name = grade.name
    grade.delete()
    messages.success(request, f"Grade '{grade_name}' deleted successfully.")
    return redirect('school_config:grades_list')


# --- Class / Section Views ---
@login_required
@user_passes_test(can_manage_academics)
def classes_list_view(request):
    classes = SchoolClass.objects.all().select_related('grade').order_by('grade__name', 'name')
    return render(request, 'school_config/classes_list.html', {'classes': classes})

@login_required
@user_passes_test(can_manage_academics)
def class_create_view(request):
    if request.method == 'POST':
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Class section created successfully.")
            return redirect('school_config:classes_list')
    else:
        form = SchoolClassForm()
    return render(request, 'school_config/class_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(can_manage_academics)
def class_edit_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, instance=school_class)
        if form.is_valid():
            form.save()
            messages.success(request, "Class section updated successfully.")
            return redirect('school_config:classes_list')
    else:
        form = SchoolClassForm(instance=school_class)
    return render(request, 'school_config/class_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(can_manage_academics)
def class_delete_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    class_name = f"{school_class.grade.name} - {school_class.name}"
    school_class.delete()
    messages.success(request, f"Class section '{class_name}' deleted successfully.")
    return redirect('school_config:classes_list')
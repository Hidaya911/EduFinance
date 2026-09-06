from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from pymongo import MongoClient
from bson.objectid import ObjectId
from .models import AcademicYear
from .forms import AcademicYearForm

ADMIN_ROLE_NAMES = {'super admin', 'super administrator', 'school administrator'}


def is_admin(user):
    """Allow only Super Admins and School Administrators into configuration."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    allowed_roles = {'Super Admin', 'Super Administrator', 'School Administrator'}
    if user.groups.filter(name__in=allowed_roles).exists():
        return True

    # Support users whose group link was saved directly in MongoDB.
    try:
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.DATABASES['default']['NAME']]
        user_ids = [user.pk, str(user.pk)]
        if ObjectId.is_valid(str(user.pk)):
            user_ids.append(ObjectId(str(user.pk)))
        user_doc = db['auth_user'].find_one({
            '$or': [{'id': {'$in': user_ids}}, {'_id': {'$in': user_ids}}]
        })
        if user_doc:
            user_ids.extend([user_doc.get('id'), user_doc.get('_id')])
        group_ids = [
            link.get('group_id') for link in db['auth_user_groups'].find(
                {'user_id': {'$in': [value for value in user_ids if value is not None]}}
            )
        ]
        return db['auth_group'].count_documents({
            '$and': [
                {'$or': [{'id': {'$in': group_ids}}, {'_id': {'$in': group_ids}}]},
                {'name': {'$in': list(allowed_roles)}},
            ]
        }) > 0
    except Exception:
        return False

@login_required
@user_passes_test(is_admin)
def academic_years_list(request):
    years = AcademicYear.objects.all().order_by('-start_date')
    return render(request, 'core/academic_years_list.html', {'years': years})

@login_required
@user_passes_test(is_admin)
def academic_year_form_view(request, pk=None):
    year = get_object_or_404(AcademicYear, pk=pk) if pk else None
    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=year)
        if form.is_valid():
            saved_year = form.save()
            if saved_year.is_current:
                # Enforce rule: only one academic year can be marked current at a time
                AcademicYear.objects.exclude(pk=saved_year.pk).update(is_current=False)
            return redirect('academic_years_list')
    else:
        form = AcademicYearForm(instance=year)
    return render(request, 'core/academic_year_form.html', {'form': form, 'is_edit': bool(pk)})

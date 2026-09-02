from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from .forms import EmailLoginForm, CustomPasswordResetForm, CustomSetPasswordForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()

from django.contrib.auth.signals import user_logged_in
user_logged_in.disconnect(dispatch_uid='update_last_login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Password reset instructions have been sent to your email.")
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been reset successfully. You can now sign in.")
        return super().form_valid(form)


def is_super_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        user_groups = [g.name for g in user.groups.all()]
        return 'Super Admin' in user_groups
    except Exception:
        return False


from django.conf import settings
from pymongo import MongoClient

from django.conf import settings
from pymongo import MongoClient
from django.contrib.auth.models import Group, Permission

@login_required
@user_passes_test(is_super_admin)
def roles_list(request):
    roles = Group.objects.all()
    roles_data = []

    # Connect to MongoDB via PyMongo
    client = MongoClient(settings.MONGO_URI if hasattr(settings, 'MONGO_URI') else settings.DATABASES['default']['CLIENT']['host'])
    db_name = settings.DATABASES['default']['NAME']
    db = client[db_name]

    raw_users = list(db['auth_user'].find({}))
    raw_groups = list(db['auth_group'].find({}))

    # Map raw group permission count from MongoDB documents
    group_perm_counts = {}
    for g in raw_groups:
        gid = str(g.get('_id'))
        perms = g.get('permissions', g.get('permissions_ids', []))
        group_perm_counts[gid] = len(perms)
        if 'id' in g:
            group_perm_counts[str(g.get('id'))] = len(perms)

    # Total system permissions count (fallback if individual role perms are unbounded/all-access)
    total_system_perms = Permission.objects.count()

    for role in roles:
        assigned_users = []
        role_str_id = str(role.pk)

        for u in raw_users:
            user_display_name = u.get('username', '')
            if u.get('first_name') or u.get('last_name'):
                user_display_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()

            if role.name == 'Super Admin' and u.get('is_superuser'):
                if user_display_name not in assigned_users:
                    assigned_users.append(user_display_name)
                    continue

            user_group_ids = [str(gid) for gid in u.get('groups_ids', u.get('groups', []))]
            if role_str_id in user_group_ids or str(role.id) in user_group_ids:
                if user_display_name not in assigned_users:
                    assigned_users.append(user_display_name)

        # Count permissions accurately
        try:
            if role.name == 'Super Admin':
                perm_count = total_system_perms
            else:
                perm_count = group_perm_counts.get(role_str_id, role.permissions.count())
        except Exception:
            perm_count = 0

        roles_data.append({
            'id': role_str_id,
            'name': role.name,
            'assigned_users': assigned_users,
            'users_count': len(assigned_users),
            'permissions_count': perm_count,
        })

    return render(request, 'accounts/roles_list.html', {'roles': roles_data})


@login_required
@user_passes_test(is_super_admin)
def delete_role(request, role_id):
    """
    Deletes a role from the system.
    """
    role = get_object_or_404(Group, pk=role_id)
    role_name = role.name
    role.delete()
    messages.success(request, f"Role '{role_name}' has been deleted successfully.")
    return redirect('roles_list')


@login_required
@user_passes_test(is_super_admin)
def role_permissions(request, role_id):
    """
    Edit permissions for a given role safely under Djongo/MongoDB.
    """
    # Fetch group via standard ORM or PyMongo fallback
    role = Group.objects.filter(pk=role_id).first()
    
    if not role:
        # Fallback PyMongo check if PK resolution fails in Djongo
        try:
            client = MongoClient(settings.MONGO_URI if hasattr(settings, 'MONGO_URI') else settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]
            raw_group = db['auth_group'].find_one({'$or': [{'_id': role_id}, {'id': role_id}]})
            if raw_group:
                role = Group.objects.filter(name=raw_group.get('name')).first()
        except Exception:
            role = None

    if not role:
        messages.error(request, "Role not found.")
        return redirect('roles_list')

    permissions = Permission.objects.all().order_by('content_type__app_label', 'codename')

    if request.method == 'POST':
        selected_permission_ids = request.POST.getlist('permissions')
        
        try:
            selected_perms = list(Permission.objects.filter(id__in=selected_permission_ids))
            role.permissions.set(selected_perms)
            messages.success(request, f"Permissions for role '{role.name}' updated successfully.")
        except Exception:
            try:
                client = MongoClient(settings.MONGO_URI if hasattr(settings, 'MONGO_URI') else settings.DATABASES['default']['CLIENT']['host'])
                db = client[settings.DATABASES['default']['NAME']]
                
                formatted_ids = [int(pid) if pid.isdigit() else pid for pid in selected_permission_ids]
                
                db['auth_group'].update_one(
                    {'$or': [{'id': role_id}, {'_id': role_id}, {'name': role.name}]},
                    {'$set': {'permissions': formatted_ids}}
                )
                messages.success(request, f"Permissions for role '{role.name}' updated successfully.")
            except Exception as ex:
                messages.error(request, f"Failed to save permissions: {str(ex)}")

        return redirect('roles_list')

    # Load permission IDs
    try:
        role_permission_ids = list(role.permissions.values_list('id', flat=True))
    except Exception:
        try:
            client = MongoClient(settings.MONGO_URI if hasattr(settings, 'MONGO_URI') else settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]
            raw_group = db['auth_group'].find_one({'$or': [{'_id': role_id}, {'id': role_id}, {'name': role.name}]})
            role_permission_ids = raw_group.get('permissions', []) if raw_group else []
        except Exception:
            role_permission_ids = []

    return render(request, 'accounts/role_permissions.html', {
        'role': role,
        'permissions': permissions,
        'role_permission_ids': set([str(p) for p in role_permission_ids])
    })
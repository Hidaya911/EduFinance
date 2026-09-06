from itertools import groupby
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import Notification, NotificationPreference

from .forms import (
    EmailLoginForm, 
    CustomPasswordResetForm, 
    CustomSetPasswordForm, 
    UserCreateForm, 
    UserEditForm,
    NotificationPreferenceForm
)

User = get_user_model()


def _mongo_id_variants(value):
    """Return the forms an identifier may have in old/new Mongo records."""
    variants = [value, str(value)]
    if str(value).isdigit():
        variants.append(int(value))
    if ObjectId.is_valid(str(value)):
        variants.append(ObjectId(str(value)))
    return variants


def _role_id_variants(role):
    variants = _mongo_id_variants(role.pk)
    if getattr(role, 'id', None) != role.pk:
        variants.extend(_mongo_id_variants(role.id))
    return variants

# Disconnect update_last_login to prevent Djongo write issues on login
user_logged_in.disconnect(dispatch_uid='update_last_login')


# EDIT: Notification data is read and written through PyMongo because the
# project already uses MongoDB directly for the auth tables. This guarantees
# notification records are stored in accounts_notification.
# EDIT: Django authentication uses auth_user.id while management screens use
# MongoDB's auth_user._id. Resolve either identifier to the same user record.
def _notification_user_record(db, user_id):
    variants = [user_id, str(user_id)]
    if str(user_id).isdigit():
        variants.append(int(user_id))
    if ObjectId.is_valid(str(user_id)):
        variants.append(ObjectId(str(user_id)))
    return db['auth_user'].find_one({
        '$or': [{'id': {'$in': variants}}, {'_id': {'$in': variants}}]
    })


# EDIT: Include both auth_user identifiers when querying notifications. This
# also makes notifications created before this fix visible to their recipients.
def _notification_id_variants(db, user_id):
    variants = [user_id, str(user_id)]
    if str(user_id).isdigit():
        variants.append(int(user_id))
    if ObjectId.is_valid(str(user_id)):
        variants.append(ObjectId(str(user_id)))

    user = _notification_user_record(db, user_id)
    if user:
        variants.extend([user.get('id'), user.get('_id'), str(user.get('id')), str(user.get('_id'))])
    return [value for value in variants if value is not None]


# EDIT: Store new records with the numeric Django user ID when available,
# matching request.user.pk and preventing future recipient-ID mismatches.
def _notification_recipient_id(db, user_id):
    user = _notification_user_record(db, user_id)
    return user.get('id', user_id) if user else user_id


# EDIT: A missing preference row uses the model defaults, so new users still
# receive in-app alerts without having to first open Notification Settings.
def _notification_is_enabled(db, user_id, preference_name):
    preference = db['accounts_notificationpreference'].find_one({
        'user_id': {'$in': _notification_id_variants(db, user_id)}
    })
    return preference is None or preference.get(preference_name, True)


# EDIT: Django's Notification model has an integer id primary key and Djongo
# enforces it with the __primary_key__ Mongo index. Repair older records that
# were inserted without an id, then calculate the next valid numeric ID.
def _next_notification_id(db):
    notifications = db['accounts_notification']
    numeric_ids = [
        document['id']
        for document in notifications.find({}, {'id': 1})
        if isinstance(document.get('id'), int) and not isinstance(document.get('id'), bool)
    ]
    next_id = max(numeric_ids, default=0) + 1

    missing_id_document = notifications.find_one({
        '$or': [{'id': {'$exists': False}}, {'id': None}]
    })
    if missing_id_document:
        notifications.update_one(
            {'_id': missing_id_document['_id']},
            {'$set': {'id': next_id}}
        )
        next_id += 1

    return next_id


# EDIT: Centralise notification inserts so every event stores the same fields
# and consistently honours the recipient's in-app notification preference.
def _create_notification(db, user_id, title, message, preference_name='system_alerts', link=None):
    recipient_id = _notification_recipient_id(db, user_id)
    if not recipient_id or not _notification_is_enabled(db, recipient_id, preference_name):
        return

    # EDIT: Include the required integer id on every direct Mongo insert. A
    # retry handles the rare case of simultaneous notifications choosing an ID.
    for _ in range(5):
        try:
            db['accounts_notification'].insert_one({
                'id': _next_notification_id(db),
                'user_id': recipient_id,
                'title': title,
                'message': message,
                'is_read': False,
                'created_at': timezone.now(),
                'link': link,
            })
            return
        except DuplicateKeyError:
            continue

    raise RuntimeError('Unable to allocate a unique notification ID.')


# EDIT: Role-permission changes affect all members of a role, so collect their
# MongoDB user IDs and notify each person once.
def _role_member_ids(db, role):
    role_ids = {str(value) for value in _role_id_variants(role)}
    member_ids = set()
    for link in db['auth_user_groups'].find({}):
        if str(link.get('group_id')) in role_ids and link.get('user_id') is not None:
            member_ids.add(link['user_id'])
    return member_ids


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
    storage = messages.get_messages(request)
    storage.used = True
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


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
    if getattr(user, 'is_superuser', False):
        return True
    try:
        client = MongoClient(
            settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
            else settings.DATABASES['default']['CLIENT']['host']
        )
        db = client[settings.DATABASES['default']['NAME']]
        
        user_id = user.pk
        raw_user = db['auth_user'].find_one({'$or': [
            {'_id': user_id}, 
            {'_id': str(user_id)}, 
            {'id': user_id}, 
            {'id': str(user_id)},
            {'username': user.username}
        ]})
        
        if raw_user and raw_user.get('is_superuser'):
            return True

        user_id_vals = {user_id, str(user_id)}
        if str(user_id).isdigit():
            user_id_vals.add(int(user_id))

        m2m_links = list(db['auth_user_groups'].find({'user_id': {'$in': list(user_id_vals)}}))
        group_ids = [link.get('group_id') for link in m2m_links]
        
        super_admin_groups = list(db['auth_group'].find({'$or': [
            {'_id': {'$in': group_ids}},
            {'id': {'$in': group_ids}},
            {'name': {'$in': ['Super Admin', 'Super Administrator']}}
        ]})) if group_ids else list(db['auth_group'].find({'name': {'$in': ['Super Admin', 'Super Administrator']}}))
        
        super_admin_group_ids = {str(g.get('_id')) for g in super_admin_groups if g.get('name') in {'Super Admin', 'Super Administrator'}}.union(
            {str(g.get('id')) for g in super_admin_groups if g.get('name') in {'Super Admin', 'Super Administrator'}}
        )
        
        for link in m2m_links:
            if str(link.get('group_id')) in super_admin_group_ids:
                return True

        if raw_user:
            for val in [raw_user.get('role'), raw_user.get('groups'), raw_user.get('group')]:
                if not val:
                    continue
                items = val if isinstance(val, list) else [val]
                for item in items:
                    if isinstance(item, dict) and item.get('name') in {'Super Admin', 'Super Administrator'}:
                        return True
                    elif str(item) in {'Super Admin', 'Super Administrator', '1'}:
                        return True
    except Exception:
        pass
        
    return False


@login_required
@user_passes_test(is_super_admin)
def roles_list(request):
    roles = Group.objects.all()
    roles_data = []
    role_name_set = {role.name for role in roles}
    # A superuser without an explicit group should appear once, under the
    # installation's canonical super-admin role, not under both aliases.
    default_super_admin_role = (
        'Super Administrator'
        if 'Super Administrator' in role_name_set
        else 'Super Admin'
    )

    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db_name = settings.DATABASES['default']['NAME']
    db = client[db_name]

    raw_users = list(db['auth_user'].find({}))
    raw_groups = list(db['auth_group'].find({}))
    raw_user_groups_m2m = list(db['auth_user_groups'].find({}))

    total_system_perms = Permission.objects.count()

    # Build one canonical membership map.  Historical records use a mix of
    # MongoDB ObjectIds, strings and legacy numeric ``id`` fields, so comparing
    # one representation (as the old code did) omitted most role members.
    group_name_by_id = {}
    for group in raw_groups:
        name = group.get('name')
        if not name:
            continue
        for identifier in (group.get('_id'), group.get('id'), name):
            if identifier is not None:
                group_name_by_id[str(identifier)] = name

    role_names_by_user_id = {}
    for link in raw_user_groups_m2m:
        user_id = link.get('user_id')
        group_name = group_name_by_id.get(str(link.get('group_id')))
        if user_id is not None and group_name:
            role_names_by_user_id.setdefault(str(user_id), set()).add(group_name)

    for role in roles:
        assigned_users = []
        assigned_user_keys = set()
        role_str_id = str(role.pk)

        for u in raw_users:
            user_id_values = {
                str(value) for value in (u.get('_id'), u.get('id'), u.get('username'))
                if value is not None
            }
            
            user_display_name = u.get('username', '')
            if u.get('first_name') or u.get('last_name'):
                user_display_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()

            user_role_names = set()
            for user_id in user_id_values:
                user_role_names.update(role_names_by_user_id.get(user_id, set()))

            raw_role_vals = [
                u.get('role'),
                u.get('role_id'),
                u.get('groups'),
                u.get('groups_ids'),
                u.get('group_id')
            ]
            
            user_group_identifiers = set()
            for val in raw_role_vals:
                if not val:
                    continue
                items = val if isinstance(val, list) else [val]

                for item in items:
                    if isinstance(item, dict):
                        user_role_names.add(str(item.get('name', '')))
                        user_group_identifiers.add(str(item.get('id', '')))
                        user_group_identifiers.add(str(item.get('_id', '')))
                    else:
                        user_role_names.add(str(item))
                        user_group_identifiers.add(str(item))

            role_match_keys = {str(value) for value in _role_id_variants(role)} | {role.name}
            is_default_super_admin_role = role.name == default_super_admin_role
            if (
                role.name in user_role_names or
                bool(user_group_identifiers.intersection(role_match_keys)) or
                (is_default_super_admin_role and u.get('is_superuser'))
            ):
                user_key = str(u.get('_id', u.get('id', u.get('username'))))
                if user_key not in assigned_user_keys:
                    assigned_user_keys.add(user_key)
                    assigned_users.append(user_display_name)

        group_id_values = _role_id_variants(role)
        perm_count = db['auth_group_permissions'].count_documents({
            'group_id': {'$in': list(group_id_values)}
        })

        if role.name == 'Super Admin' and perm_count == 0:
            perm_count = total_system_perms

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
    try:
        role = Group.objects.get(pk=role_id)
    except (Group.DoesNotExist, ValueError):
        role = get_object_or_404(Group, id=role_id)

    role_name = role.name
    role.delete()
    messages.success(request, f"Role '{role_name}' has been deleted successfully.")
    return redirect('accounts:roles_list')


@login_required
@user_passes_test(is_super_admin)
def role_permissions(request, role_id):
    try:
        role = Group.objects.get(pk=role_id)
    except (Group.DoesNotExist, ValueError):
        role = get_object_or_404(Group, id=role_id)

    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]

    if request.method == 'POST':
        # MongoDB permission identifiers may be ObjectIds, not integers.
        # Preserve the posted identifiers exactly as rendered by the form.
        selected_ids = []
        for permission_id in request.POST.getlist('permissions'):
            if not permission_id:
                continue
            permission = db['auth_permission'].find_one({'$or': [
                {'_id': {'$in': _mongo_id_variants(permission_id)}},
                {'id': {'$in': _mongo_id_variants(permission_id)}},
            ]})
            # Store the identifier type used by the permission document so
            # Django's permission backend can resolve the relation as well.
            selected_ids.append(
                permission.get('id', permission.get('_id', permission_id))
                if permission else permission_id
            )

        db['auth_group_permissions'].delete_many({
            'group_id': {'$in': _role_id_variants(role)}
        })
        if selected_ids:
            db['auth_group_permissions'].insert_many([
                {'group_id': role.pk, 'permission_id': pid} for pid in selected_ids
            ])
        # EDIT: Inform users whose role changed, and the administrator who made
        # the change, after the new permission links were saved successfully.
        recipients = _role_member_ids(db, role)
        recipients.add(request.user.pk)
        for recipient_id in recipients:
            _create_notification(
                db,
                recipient_id,
                'Role permissions updated',
                f"Permissions for the {role.name} role were updated.",
                preference_name='role_updates',
                link=reverse('accounts:role_permissions', kwargs={'role_id': role.pk}),
            )
        messages.success(request, f"Permissions updated for {role.name}.")
        return redirect('accounts:roles_list')

    content_types = {ct['_id']: ct for ct in db['django_content_type'].find({})}

    raw_permissions = list(db['auth_permission'].find({}))
    for perm in raw_permissions:
        ct = content_types.get(perm.get('content_type_id'))
        perm['app_label'] = ct.get('app_label', '') if ct else ''

    raw_permissions.sort(key=lambda p: (p.get('app_label', ''), p.get('codename', '')))

    grouped_permissions = [
        {'grouper': app_label, 'list': list(items)}
        for app_label, items in groupby(raw_permissions, key=lambda p: p['app_label'])
    ]

    role_permission_ids = set()
    query_conditions = [{'group_id': value} for value in _role_id_variants(role)]
    query_conditions.append({'group_name': role.name})

    perm_links = db['auth_group_permissions'].find({'$or': query_conditions})
    for link in perm_links:
        pid = link.get('permission_id')
        if pid is not None:
            role_permission_ids.add(pid)
            if str(pid).isdigit():
                role_permission_ids.add(int(pid))

    return render(request, 'accounts/role_permissions.html', {
        'role': role,
        'grouped_permissions': grouped_permissions,
        'role_permission_ids': role_permission_ids,
    })


@login_required
@user_passes_test(is_super_admin)
def users_list(request):
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]

    raw_users = list(db['auth_user'].find({}))
    raw_groups = list(db['auth_group'].find({}))
    raw_m2m = list(db['auth_user_groups'].find({}))

    group_map = {}
    for g in raw_groups:
        g_name = g.get('name')
        if '_id' in g:
            group_map[str(g['_id'])] = g_name
        if 'id' in g:
            group_map[str(g['id'])] = g_name

    users_data = []
    for u in raw_users:
        u_id = str(u.get('_id', u.get('id', '')))
        username = u.get('username', '')
        
        role_name = "No Role"

        if u.get('is_superuser'):
            role_name = "Super Admin"

        if role_name == "No Role":
            for m in raw_m2m:
                m_user_id = str(m.get('user_id', ''))
                m_group_id = str(m.get('group_id', ''))
                
                if m_user_id in {u_id, str(u.get('id', '')), username}:
                    if m_group_id in group_map:
                        role_name = group_map[m_group_id]
                        break

        if role_name == "No Role":
            raw_role_vals = [u.get('role'), u.get('groups'), u.get('group')]
            for val in raw_role_vals:
                if not val:
                    continue
                items = val if isinstance(val, list) else [val]
                for item in items:
                    if isinstance(item, dict):
                        role_name = item.get('name', role_name)
                    elif isinstance(item, str) and item:
                        role_name = item

        full_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()

        users_data.append({
            'id': u_id,
            'username': username,
            'email': u.get('email', ''),
            'full_name': full_name or username,
            'role_name': role_name,
            'is_active': u.get('is_active', True),
        })

    return render(request, 'accounts/users_list.html', {'users': users_data})


@login_required
@user_passes_test(is_super_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            # EDIT: Record user creation for the new account and the creating
            # administrator, using the default enabled preferences when absent.
            client = MongoClient(
                settings.MONGO_URI if hasattr(settings, 'MONGO_URI')
                else settings.DATABASES['default']['CLIENT']['host']
            )
            db = client[settings.DATABASES['default']['NAME']]
            _create_notification(
                db,
                user.pk,
                'Welcome to EduFinance',
                'Your account was created by an administrator.',
                link=reverse('accounts:notification_settings'),
            )
            if str(request.user.pk) != str(user.pk):
                _create_notification(
                    db,
                    request.user.pk,
                    'User created',
                    f"You created the account for {user.username}.",
                    link=reverse('accounts:users_list'),
                )
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('accounts:users_list')
    else:
        storage = messages.get_messages(request)
        storage.used = True
        form = UserCreateForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create New User',
        'btn_text': 'Create User',
    })


def _get_user_by_id_or_mongodb(user_id):
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]
    
    query_conditions = []
    if ObjectId.is_valid(user_id):
        query_conditions.append({'_id': ObjectId(user_id)})
    query_conditions.append({'_id': str(user_id)})
    if str(user_id).isdigit():
        query_conditions.append({'id': int(user_id)})
    query_conditions.append({'id': str(user_id)})

    raw_user = db['auth_user'].find_one({'$or': query_conditions})
    if raw_user:
        return raw_user
    raise ValueError(f"User with ID {user_id} does not exist.")


@login_required
@user_passes_test(is_super_admin)
def user_edit(request, user_id):
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]

    try:
        raw_user = _get_user_by_id_or_mongodb(user_id)
    except ValueError:
        messages.error(request, "User not found.")
        return redirect('accounts:users_list')

    class DummyUser:
        def __init__(self, data):
            self.pk = data.get('_id', data.get('id'))
            self.id = self.pk
            self.username = data.get('username')
            self.email = data.get('email')
            self.first_name = data.get('first_name', '')
            self.last_name = data.get('last_name', '')
            self.is_active = data.get('is_active', True)
            self.is_superuser = data.get('is_superuser', False)

    user_dummy = DummyUser(raw_user)

    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            # EDIT: Preserve the old values so the notification accurately
            # describes the account update after MongoDB has been changed.
            old_role_link = db['auth_user_groups'].find_one({
                'user_id': {'$in': _mongo_id_variants(raw_user['_id']) + _mongo_id_variants(raw_user.get('id', raw_user['_id']))}
            })
            update_data = {
                'username': form.cleaned_data.get('username'),
                'email': form.cleaned_data.get('email'),
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
                'is_active': form.cleaned_data.get('is_active', False),
            }
            if form.cleaned_data.get('password'):
                update_data['password'] = make_password(form.cleaned_data.get('password'))

            db['auth_user'].update_one(
                {'_id': raw_user['_id']},
                {'$set': update_data}
            )

            role = form.cleaned_data.get('role')
            db['auth_user_groups'].delete_many({
                'user_id': {'$in': _mongo_id_variants(raw_user['_id']) + _mongo_id_variants(raw_user.get('id', raw_user['_id']))}
            })
            if role:
                db['auth_user_groups'].insert_one({
                    'user_id': raw_user['_id'],
                    'group_id': role.pk
                })

            # EDIT: Create an in-app record for the edited user and a separate
            # audit alert for the admin performing the update. This is written
            # directly to accounts_notification and therefore appears in the UI.
            role_changed = (str(old_role_link.get('group_id')) if old_role_link else None) != (
                str(role.pk) if role else None
            )
            target_title = 'Your role was updated' if role_changed else 'Your account was updated'
            target_message = (
                f"Your system role is now {role.name if role else 'not assigned'}."
                if role_changed else 'An administrator updated your account details.'
            )
            _create_notification(
                db,
                raw_user['_id'],
                target_title,
                target_message,
                preference_name='role_updates' if role_changed else 'system_alerts',
                link=reverse('accounts:notification_settings'),
            )
            if str(request.user.pk) != str(raw_user['_id']):
                _create_notification(
                    db,
                    request.user.pk,
                    'User updated',
                    f"You updated the account for {update_data['username']}.",
                    link=reverse('accounts:users_list'),
                )

            messages.success(request, f"User '{user_dummy.username}' updated successfully.")
            return redirect('accounts:users_list')
    else:
        storage = messages.get_messages(request)
        storage.used = True
        
        current_group_link = db['auth_user_groups'].find_one({
            'user_id': {'$in': _mongo_id_variants(raw_user['_id']) + _mongo_id_variants(raw_user.get('id', raw_user['_id']))}
        })
        initial_role = None
        if current_group_link:
            group_doc = db['auth_group'].find_one({'$or': [
                {'_id': {'$in': _mongo_id_variants(current_group_link['group_id'])}},
                {'id': {'$in': _mongo_id_variants(current_group_link['group_id'])}},
            ]})
            if group_doc:
                initial_role = Group.objects.filter(name=group_doc.get('name')).first()

        form = UserEditForm(initial={
            'username': user_dummy.username,
            'email': user_dummy.email,
            'first_name': user_dummy.first_name,
            'last_name': user_dummy.last_name,
            'is_active': user_dummy.is_active,
            'role': initial_role,
        })

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'user_obj': user_dummy,
        'title': f"Edit User: {user_dummy.username}",
        'btn_text': 'Save Changes',
    })


@login_required
@user_passes_test(is_super_admin)
def user_toggle_status(request, user_id):
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]

    query_conditions = []
    if ObjectId.is_valid(user_id):
        query_conditions.append({'_id': ObjectId(user_id)})
    query_conditions.append({'_id': str(user_id)})
    if str(user_id).isdigit():
        query_conditions.append({'id': int(user_id)})
    query_conditions.append({'id': str(user_id)})

    raw_user = db['auth_user'].find_one({'$or': query_conditions})
    if not raw_user:
        messages.error(request, "User not found.")
        return redirect('accounts:users_list')

    new_status = not raw_user.get('is_active', True)
    
    db['auth_user'].update_one(
        {'_id': raw_user['_id']},
        {'$set': {'is_active': new_status}}
    )

    # EDIT: Store status-change alerts for both the affected user and the
    # administrator, respecting each recipient's system-alert preference.
    status_text = 'activated' if new_status else 'deactivated'
    _create_notification(
        db,
        raw_user['_id'],
        f'Account {status_text}',
        f'Your account has been {status_text} by an administrator.',
        link=reverse('accounts:notification_settings'),
    )
    if str(request.user.pk) != str(raw_user['_id']):
        _create_notification(
            db,
            request.user.pk,
            f'User {status_text}',
            f"You {status_text} the account for {raw_user.get('username', 'a user')}.",
            link=reverse('accounts:users_list'),
        )

    username = raw_user.get('username', 'User')
    status_str = "activated" if new_status else "deactivated"
    messages.success(request, f"User '{username}' has been {status_str}.")
    return redirect('accounts:users_list')


@login_required
def notifications_list(request):
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db = client[settings.DATABASES['default']['NAME']]

    # EDIT: Query with both the session's numeric ID and the MongoDB _id so
    # notifications for accounts edited through either path are displayed.
    user_id_vals = _notification_id_variants(db, request.user.pk)
    user_id_strings = {str(user_id) for user_id in user_id_vals}

    if request.GET.get('mark_all_read') == 'true':
        # EDIT: Compare normalized IDs in Python because Djongo may mix integer
        # primary keys and ObjectIds in the same user_id MongoDB index.
        unread_notifications = db['accounts_notification'].find({'is_read': False})
        for notification in unread_notifications:
            if str(notification.get('user_id')) in user_id_strings:
                db['accounts_notification'].update_one(
                    {'_id': notification['_id']},
                    {'$set': {'is_read': True}}
                )
        return redirect('accounts:notifications_list')

    # EDIT: Filter normalized IDs after reading because this reliably includes
    # legacy ObjectId notifications and new numeric-ID notifications together.
    raw_notifications = [
        notification
        for notification in db['accounts_notification'].find({})
        if str(notification.get('user_id')) in user_id_strings
    ]
    raw_notifications.sort(key=lambda notification: notification.get('created_at') or timezone.now(), reverse=True)

    notifications = []
    for notif in raw_notifications:
        notifications.append({
            'title': notif.get('title', ''),
            'message': notif.get('message', ''),
            'is_read': notif.get('is_read', False),
            'created_at': notif.get('created_at'),
            'link': notif.get('link', None),
        })

    return render(request, 'accounts/notifications_list.html', {
        'notifications': notifications
    })


@login_required
def notification_settings(request):
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully.")
            return redirect('accounts:notification_settings')
    else:
        form = NotificationPreferenceForm(instance=prefs)

    return render(request, 'accounts/notification_settings.html', {
        'form': form
    })

@login_required
def profile_settings_view(request):
    User = get_user_model()
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user = request.user
            new_username = request.POST.get('username', '').strip()
            
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, "This username is already taken.")
                    return redirect('accounts:profile_settings')
                user.username = new_username

            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            # Trigger notification for the notification side panel
            # Notification.objects.create(
            #     user=user, 
            #     title="Profile Updated", 
            #     message="Your account credentials and personal details were modified successfully."
            # )

            messages.success(request, "Your profile settings have been updated successfully.")
            return redirect('accounts:profile_settings')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                
                # Trigger notification for password change
                # Notification.objects.create(
                #     user=user, 
                #     title="Password Changed", 
                #     message="Your account security password was recently updated."
                # )

                messages.success(request, "Your password has been changed successfully.")
                return redirect('accounts:profile_settings')
            else:
                messages.error(request, "Please check the password error messages below.")

    context = {
        'password_form': password_form,
    }
    return render(request, 'accounts/profile_settings.html', context)
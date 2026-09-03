from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import Group
from django.conf import settings
from pymongo import MongoClient
from .models import NotificationPreference

User = get_user_model()


def _get_mongo_db():
    client = MongoClient(
        settings.MONGO_URI if hasattr(settings, 'MONGO_URI') 
        else settings.DATABASES['default']['CLIENT']['host']
    )
    db_name = settings.DATABASES['default']['NAME']
    return client[db_name]


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'amal@springfield.edu',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••••••'})
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••••••'})
    )


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••••••'}),
        required=True
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Role"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            role = self.cleaned_data.get('role')
            db = _get_mongo_db()

            # Clear existing group records
            db['auth_user_groups'].delete_many({
                '$or': [
                    {'user_id': user.pk},
                    {'user_id': str(user.pk)}
                ]
            })

            # Save group record via PyMongo
            if role:
                role_pk = getattr(role, 'pk', getattr(role, 'id', None))
                db['auth_user_groups'].insert_one({
                    'user_id': str(user.pk),
                    'group_id': str(role_pk)
                })

        return user

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['email_notifications', 'system_alerts', 'role_updates']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'system_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'role_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
# EDIT: This must be a regular Form, not a ModelForm.  The edit view writes
# directly to MongoDB, and a ModelForm with the view's lightweight user object
# can be treated as a new Django user and create a second auth_user document.
class UserEditForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current password'}),
        required=False
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Role"
    )

    # EDIT: Define explicit fields because this form intentionally has no
    # ModelForm Meta/save method; the view performs one targeted Mongo update.
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


  


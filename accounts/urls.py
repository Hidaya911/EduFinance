from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset URLs
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # Roles URLs
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/<str:role_id>/permissions/', views.role_permissions, name='role_permissions'),
    path('roles/<str:role_id>/delete/', views.delete_role, name='delete_role'),

    # Users Management URLs
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<str:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<str:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    #profile settings
    path('profile/', views.profile_settings_view, name='profile_settings'),
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/settings/', views.notification_settings, name='notification_settings'),
]
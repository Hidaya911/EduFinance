from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('roles/', views.roles_list, name='roles_list'),
    # Use <str:role_id> rather than <int:role_id>
   path('roles/<str:role_id>/permissions/', views.role_permissions, name='role_permissions'),
   path('roles/<str:role_id>/delete/', views.delete_role, name='delete_role'),
]
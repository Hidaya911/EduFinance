from django.urls import path

from . import views
from .views import (
    fee_categories_list_view, 
    fee_category_create_view, 
    fee_category_edit_view,
    fee_category_toggle_status_view,
    fee_category_delete_view
)

app_name = "school_config"


urlpatterns = [
    path(
        "settings/",
        views.school_settings,
        name="school_settings",
    ),
    path('fee-categories/', fee_categories_list_view, name='fee_categories_list'),
    path('fee-categories/add/', fee_category_create_view, name='fee_category_create'),
    # MongoDB uses ObjectId primary keys, so this uses str to handle string/ObjectId matching correctly.
    path('fee-categories/<str:pk>/edit/', fee_category_edit_view, name='fee_category_edit'),
    path('fee-categories/<str:pk>/toggle/', fee_category_toggle_status_view, name='fee_category_toggle'),
    path('fee-categories/<str:pk>/delete/', fee_category_delete_view, name='fee_category_delete'),

# Grades URLs
    path('grades/', views.grades_list_view, name='grades_list'),
    path('grades/add/', views.grade_create_view, name='grade_create'),
    path('grades/<str:pk>/edit/', views.grade_edit_view, name='grade_edit'),
    path('grades/<str:pk>/delete/', views.grade_delete_view, name='grade_delete'),

    # Classes URLs
    path('classes/', views.classes_list_view, name='classes_list'),
    path('classes/add/', views.class_create_view, name='class_create'),
    path('classes/<str:pk>/edit/', views.class_edit_view, name='class_edit'),
    path('classes/<str:pk>/delete/', views.class_delete_view, name='class_delete'),


]
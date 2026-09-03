from django.urls import path

from . import views


urlpatterns = [
    path('academic-years/', views.academic_years_list, name='academic_years_list'),
    path('academic-years/create/', views.academic_year_form_view, name='academic_year_create'),
    path('academic-years/<str:pk>/edit/', views.academic_year_form_view, name='academic_year_edit'),
]

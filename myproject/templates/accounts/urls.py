from django.urls import path
from . import views

urlpatterns = [
    path('preview/', views.base_preview_view, name='base_preview'),
]
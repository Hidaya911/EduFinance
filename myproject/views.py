# myproject/views.py
from django.shortcuts import render

def base_preview_view(request):
    return render(request, 'accounts/preview.html')

def dashboard_view(request):
     return render(request, 'dashboard.html')
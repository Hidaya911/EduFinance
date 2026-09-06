from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.core.models import AcademicYear
from billing.forms import FeeStructureForm, FeeStructureItemFormSet
from billing.models import FeeStructure
from billing.permissions import fee_structure_access_required
from school_config.models import Grade
from .helpers import get_current_school
@fee_structure_access_required
def fee_structure_list(request):
    school=get_current_school(); structures=FeeStructure.objects.filter(school=school); search=request.GET.get("q","").strip(); year=request.GET.get("academic_year",""); grade=request.GET.get("grade",""); status=request.GET.get("status","")
    if search: structures=structures.filter(Q(name__icontains=search)|Q(grade__name__icontains=search)|Q(academic_year__name__icontains=search))
    if year: structures=structures.filter(academic_year_id=year)
    if grade: structures=structures.filter(grade_id=grade)
    if status=="active": structures=structures.filter(is_active=True)
    elif status=="inactive": structures=structures.filter(is_active=False)
    context={"structures":structures.order_by("-created_at"),"academic_years":AcademicYear.objects.all().order_by("-start_date"),"grades":Grade.objects.all().order_by("name"),"search":search,"selected_academic_year":year,"selected_grade":grade,"selected_status":status}
    if request.headers.get("X-Requested-With")=="XMLHttpRequest": return render(request,"billing/fee_structures/partials/results.html",context)
    return render(request,"billing/fee_structures/list.html",context)
@fee_structure_access_required
def fee_structure_create(request):
    school=get_current_school(); structure=FeeStructure(school=school,created_by=request.user)
    if request.method=="POST":
        form=FeeStructureForm(request.POST,instance=structure); formset=FeeStructureItemFormSet(request.POST,instance=structure)
        if form.is_valid() and formset.is_valid():
            structure=form.save(commit=False); structure.school=school; structure.created_by=request.user; structure.save(); formset.instance=structure; formset.save(); structure.recalculate_total(); messages.success(request,"Fee structure created successfully."); return redirect("billing:fee_structure_list")
    else: form=FeeStructureForm(instance=structure); formset=FeeStructureItemFormSet(instance=structure)
    return render(request,"billing/fee_structures/form.html",{"form":form,"formset":formset,"page_title":"Create Fee Structure","submit_text":"Create Fee Structure"})
@fee_structure_access_required
def fee_structure_edit(request,pk):
    school=get_current_school(); structure=get_object_or_404(FeeStructure,pk=pk,school=school)
    if request.method=="POST":
        form=FeeStructureForm(request.POST,instance=structure); formset=FeeStructureItemFormSet(request.POST,instance=structure)
        if form.is_valid() and formset.is_valid(): structure=form.save(commit=False); structure.school=school; structure.save(); formset.save(); structure.recalculate_total(); messages.success(request,"Fee structure updated successfully."); return redirect("billing:fee_structure_list")
    else: form=FeeStructureForm(instance=structure); formset=FeeStructureItemFormSet(instance=structure)
    return render(request,"billing/fee_structures/form.html",{"form":form,"formset":formset,"structure":structure,"page_title":"Edit Fee Structure","submit_text":"Save Changes"})
@fee_structure_access_required
def fee_structure_toggle(request,pk):
    if request.method!="POST": raise PermissionDenied
    s=get_object_or_404(FeeStructure,pk=pk,school=get_current_school()); s.is_active=not s.is_active; s.save(update_fields=["is_active","updated_at"]); messages.success(request,"Fee structure status updated."); return redirect("billing:fee_structure_list")

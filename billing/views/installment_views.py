from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404,redirect,render
from billing.forms import InstallmentPlanForm,InstallmentFormSet
from billing.models import InstallmentPlan
from billing.permissions import installment_manage_required
from .helpers import get_current_school
@installment_manage_required
def installment_plan_list(request):
    qs=InstallmentPlan.objects.filter(school=get_current_school()); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(student__first_name__icontains=q)|Q(student__last_name__icontains=q)|Q(invoice__invoice_number__icontains=q))
    return render(request,"billing/installments/list.html",{"plans":qs.order_by("-created_at"),"q":q})
@installment_manage_required
def installment_plan_create(request):
    school=get_current_school(); plan=InstallmentPlan(school=school,created_by=request.user)
    if request.method=="POST":
        form=InstallmentPlanForm(request.POST,instance=plan)
        if form.is_valid():
            inv=form.cleaned_data["invoice"]; plan.student=inv.student; plan.academic_year=inv.academic_year; plan.total_amount=form.cleaned_data["total_amount"]
        formset=InstallmentFormSet(request.POST,instance=plan)
        if form.is_valid() and formset.is_valid():
            inv=form.cleaned_data["invoice"]; plan=form.save(commit=False); plan.school=school; plan.student=inv.student; plan.academic_year=inv.academic_year; plan.created_by=request.user; plan.save(); formset.instance=plan
            installments=formset.save(commit=False)
            for n,inst in enumerate(installments,start=1): inst.installment_number=n; inst.save(); inst.refresh_status()
            messages.success(request,"Installment plan created."); return redirect("billing:installment_plan_detail",pk=plan.pk)
    else: form=InstallmentPlanForm(instance=plan); formset=InstallmentFormSet(instance=plan)
    return render(request,"billing/installments/form.html",{"form":form,"formset":formset})
@installment_manage_required
def installment_plan_detail(request,pk):
    plan=get_object_or_404(InstallmentPlan,pk=pk,school=get_current_school())
    for inst in plan.installments.all(): inst.refresh_status()
    return render(request,"billing/installments/detail.html",{"plan":plan})

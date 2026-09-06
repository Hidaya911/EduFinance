from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from billing.forms import PaymentForm,PaymentAllocationFormSet
from billing.models import Payment
from billing.permissions import payment_manage_required
from billing.services import record_payment
from .helpers import get_current_school
@payment_manage_required
def payment_list(request):
    qs=Payment.objects.filter(school=get_current_school()); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(payment_number__icontains=q)|Q(student__first_name__icontains=q)|Q(student__last_name__icontains=q)|Q(student__student_number__icontains=q))
    return render(request,"billing/payments/list.html",{"payments":qs.order_by("-payment_date","-created_at"),"q":q})
@payment_manage_required
def payment_create(request):
    school=get_current_school(); initial={"payment_date":timezone.localdate()}
    if request.GET.get("student"): initial["student"]=request.GET["student"]
    selected=None
    if request.method=="POST":
        form=PaymentForm(request.POST)
        if form.is_valid(): selected=form.cleaned_data["student"]
        formset=PaymentAllocationFormSet(request.POST,prefix="alloc",form_kwargs={"student":selected})
        if form.is_valid() and formset.is_valid():
            allocations=[]
            for af in formset:
                d=getattr(af,"cleaned_data",None)
                if d and not d.get("DELETE") and d.get("invoice") and d.get("amount"): allocations.append((d["invoice"],d["amount"]))
            try: payment=record_payment(school=school,student=form.cleaned_data["student"],payment_date=form.cleaned_data["payment_date"],payment_method=form.cleaned_data["payment_method"],allocations=allocations,received_by=request.user,notes=form.cleaned_data["notes"])
            except ValueError as exc: form.add_error(None,str(exc))
            else: messages.success(request,f"Payment {payment.payment_number} recorded."); return redirect("billing:payment_detail",pk=payment.pk)
    else: form=PaymentForm(initial=initial); formset=PaymentAllocationFormSet(prefix="alloc",form_kwargs={"student":None})
    return render(request,"billing/payments/form.html",{"form":form,"formset":formset})
@payment_manage_required
def payment_detail(request,pk): return render(request,"billing/payments/detail.html",{"payment":get_object_or_404(Payment,pk=pk,school=get_current_school())})

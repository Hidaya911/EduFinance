from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404,redirect,render
from billing.forms import InvoiceCreateForm
from billing.models import Invoice
from billing.permissions import invoice_manage_required,invoice_view_required
from billing.services import create_invoice_from_fee_structure
from .helpers import get_current_school
@invoice_view_required
def invoice_list(request):
    qs=Invoice.objects.filter(school=get_current_school()); q=request.GET.get("q","").strip(); status=request.GET.get("status","")
    if q: qs=qs.filter(Q(invoice_number__icontains=q)|Q(student__first_name__icontains=q)|Q(student__last_name__icontains=q)|Q(student__student_number__icontains=q))
    if status: qs=qs.filter(status=status)
    return render(request,"billing/invoices/list.html",{"invoices":qs.order_by("-created_at"),"q":q,"selected_status":status,"status_choices":Invoice.STATUS_CHOICES})
@invoice_manage_required
def invoice_create(request):
    school=get_current_school(); initial={};
    if request.GET.get("student"): initial["student"]=request.GET["student"]
    if request.method=="POST":
        form=InvoiceCreateForm(request.POST,school=school)
        if form.is_valid():
            try: invoice=create_invoice_from_fee_structure(school=school,student=form.cleaned_data["student"],enrollment=form.cleaned_data["enrollment"],academic_year=form.cleaned_data["academic_year"],fee_structure=form.cleaned_data["fee_structure"],due_date=form.cleaned_data["due_date"],created_by=request.user)
            except ValueError as exc: form.add_error(None,str(exc))
            else: messages.success(request,f"Invoice {invoice.invoice_number} created."); return redirect("billing:invoice_detail",pk=invoice.pk)
    else: form=InvoiceCreateForm(initial=initial,school=school)
    return render(request,"billing/invoices/form.html",{"form":form})
@invoice_view_required
def invoice_detail(request,pk): return render(request,"billing/invoices/detail.html",{"invoice":get_object_or_404(Invoice,pk=pk,school=get_current_school())})
@invoice_manage_required
def invoice_void(request,pk):
    invoice=get_object_or_404(Invoice,pk=pk,school=get_current_school())
    if request.method=="POST":
        if invoice.paid_amount>0: messages.error(request,"A paid/partially paid invoice cannot be voided directly.")
        else: invoice.status=Invoice.STATUS_VOID; invoice.save(update_fields=["status","updated_at"]); messages.success(request,"Invoice voided.")
    return redirect("billing:invoice_detail",pk=invoice.pk)

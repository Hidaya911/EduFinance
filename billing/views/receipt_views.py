from django.db.models import Q
from django.shortcuts import get_object_or_404,render
from billing.models import Receipt
from billing.permissions import receipt_view_required
from .helpers import get_current_school
@receipt_view_required
def receipt_list(request):
    qs=Receipt.objects.filter(school=get_current_school()); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(receipt_number__icontains=q)|Q(payment__payment_number__icontains=q)|Q(student__first_name__icontains=q)|Q(student__last_name__icontains=q))
    return render(request,"billing/receipts/list.html",{"receipts":qs.order_by("-issued_at"),"q":q})
@receipt_view_required
def receipt_detail(request,pk): return render(request,"billing/receipts/detail.html",{"receipt":get_object_or_404(Receipt,pk=pk,school=get_current_school())})

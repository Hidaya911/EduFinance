from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render
from billing.models import Receipt, Payment
from billing.permissions import receipt_view_required
from billing.services.receipt_service import receipt_queryset, receipt_document_context
from .helpers import get_current_school


@login_required(login_url="accounts:login")
@receipt_view_required
def receipt_list(request):
    school = get_current_school()
    records = Receipt.objects.filter(school=school)
    valid = records.filter(status="issued", payment__status="completed")
    summary = {"count": records.count(), "issued": valid.count(),
               "void": records.filter(Q(status="void") | Q(payment__status="void")).count(),
               "amount": valid.aggregate(total=Sum("amount"))["total"] or 0}
    qs = receipt_queryset(school)
    q, status, method = request.GET.get("q", "").strip(), request.GET.get("status", ""), request.GET.get("method", "")
    if q:
        qs = qs.filter(Q(receipt_number__icontains=q) | Q(payment__payment_number__icontains=q) |
                       Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) |
                       Q(student__student_number__icontains=q))
    if status == "issued":
        qs = qs.filter(status="issued", payment__status="completed")
    elif status == "void":
        qs = qs.filter(Q(status="void") | Q(payment__status="void"))
    if method in dict(Payment.METHOD_CHOICES):
        qs = qs.filter(payment__payment_method=method)
    date_error = ""
    for name, lookup in (("date_from", "payment__payment_date__gte"), ("date_to", "payment__payment_date__lte")):
        raw = request.GET.get(name, "")
        if raw:
            try:
                qs = qs.filter(**{lookup: date.fromisoformat(raw)})
            except ValueError:
                date_error = "Enter dates in YYYY-MM-DD format."
    page = Paginator(qs.order_by("-issued_at", "-pk"), 20).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "billing/receipts/list.html", {
        "receipts": page, "page_obj": page, "summary": summary,
        "currency_code": school.default_currency, "q": q, "status": status, "method": method,
        "method_choices": Payment.METHOD_CHOICES, "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""), "date_error": date_error,
        "filter_query": params.urlencode(),
    })


def _receipt_context(pk):
    receipt = get_object_or_404(receipt_queryset(get_current_school()), pk=pk)
    return receipt_document_context(receipt)


@login_required(login_url="accounts:login")
@receipt_view_required
def receipt_detail(request, pk):
    return render(request, "billing/receipts/detail.html", _receipt_context(pk))


@login_required(login_url="accounts:login")
@receipt_view_required
def receipt_print(request, pk):
    context = _receipt_context(pk)
    context["auto_print"] = request.GET.get("print") == "1"
    return render(request, "billing/receipts/print.html", context)

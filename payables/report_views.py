"""Views and safe exports for the read-only Reports workspace."""

import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .report_services import (
    build_report,
    get_report_definition,
    get_reports_catalog,
    get_school_context,
)


PAGE_SIZE = 25


def _query_string(request, exclude=()):
    params = request.GET.copy()
    for key in exclude:
        params.pop(key, None)
    return params.urlencode()


def _csv_safe(value):
    text = str(value if value is not None else "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


@login_required
def reports_hub(request):
    catalog = get_reports_catalog()
    context = {
        **catalog,
        **get_school_context(),
        "total_reports": len(catalog["reports"]),
        "as_of": timezone.localtime(),
    }
    return render(request, "payables/reports_hub.html", context)


@login_required
def report_detail(request, slug):
    definition = get_report_definition(slug)
    if not definition:
        raise Http404("Report not found")

    school_context = get_school_context()
    result = build_report(slug, request.GET, school_context["currency_code"])
    paginator = Paginator(result["rows"], PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        **result,
        **school_context,
        "page_obj": page,
        "visible_rows": page.object_list,
        "filtered_count": paginator.count,
        "as_of": timezone.localtime(),
        "preserved_query": _query_string(request, ("page",)),
        "export_query": _query_string(request, ("page",)),
    }
    return render(request, "payables/reports/report_detail.html", context)


@login_required
def report_csv_export(request, slug):
    definition = get_report_definition(slug)
    if not definition:
        raise Http404("Report not found")

    school_context = get_school_context()
    result = build_report(slug, request.GET, school_context["currency_code"])
    if not result["export_enabled"]:
        raise Http404("Export is unavailable until this report's integration is complete")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{definition["id"].lower()}-{slug}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow([_csv_safe(value) for value in result["columns"]])
    for row in result["rows"]:
        writer.writerow([_csv_safe(value) for value in row["export"]])
    return response

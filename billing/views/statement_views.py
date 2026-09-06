from datetime import datetime
from django.shortcuts import get_object_or_404,render
from billing.permissions import statement_view_required
from billing.services import build_student_statement
from students.models import Student
def _parse_date(v):
    if not v: return None
    try: return datetime.strptime(v,"%Y-%m-%d").date()
    except ValueError: return None
@statement_view_required
def statement_list(request): return render(request,"billing/statements/list.html",{"students":Student.objects.order_by("first_name","last_name")})
@statement_view_required
def student_statement(request,student_pk):
    s=get_object_or_404(Student,pk=student_pk); start=_parse_date(request.GET.get("start_date")); end=_parse_date(request.GET.get("end_date")); c=build_student_statement(s,start_date=start,end_date=end); c.update({"start_date":start,"end_date":end}); return render(request,"billing/statements/detail.html",c)

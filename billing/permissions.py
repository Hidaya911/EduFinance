from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
SUPER_NAMES={"Super Administrator","Super Admin"}
def _roles(user):
    names=set(user.groups.values_list("name",flat=True)); role=getattr(user,"role",None)
    if role: names.add(str(role))
    return names
def role_required(*allowed):
    def deco(view):
        @login_required
        @wraps(view)
        def wrapper(request,*args,**kwargs):
            u=request.user
            if u.is_superuser or (_roles(u)&SUPER_NAMES) or (_roles(u)&set(allowed)): return view(request,*args,**kwargs)
            raise PermissionDenied
        return wrapper
    return deco
fee_structure_access_required=role_required("School Administrator","School Admin","Accountant")
invoice_manage_required=role_required("Accountant")
invoice_view_required=role_required("School Administrator","School Admin","Accountant","Cashier","Auditor","Read-Only")
payment_manage_required=role_required("Accountant","Cashier")
installment_manage_required=role_required("Accountant")
receipt_view_required=role_required("Accountant","Cashier","Auditor","Read-Only")
statement_view_required=role_required("Accountant","Auditor","Read-Only")
from django.urls import path
from billing import views
app_name="billing"
urlpatterns=[
path("fee-structures/",views.fee_structure_list,name="fee_structure_list"),path("fee-structures/create/",views.fee_structure_create,name="fee_structure_create"),path("fee-structures/<str:pk>/edit/",views.fee_structure_edit,name="fee_structure_edit"),path("fee-structures/<str:pk>/toggle/",views.fee_structure_toggle,name="fee_structure_toggle"),
path("invoices/",views.invoice_list,name="invoice_list"),path("invoices/create/",views.invoice_create,name="invoice_create"),path("invoices/<str:pk>/",views.invoice_detail,name="invoice_detail"),path("invoices/<str:pk>/void/",views.invoice_void,name="invoice_void"),
path("payments/",views.payment_list,name="payment_list"),path("payments/create/",views.payment_create,name="payment_create"),path("payments/<str:pk>/",views.payment_detail,name="payment_detail"),
path("installments/",views.installment_plan_list,name="installment_plan_list"),path("installments/create/",views.installment_plan_create,name="installment_plan_create"),path("installments/<str:pk>/",views.installment_plan_detail,name="installment_plan_detail"),
path("receipts/",views.receipt_list,name="receipt_list"),path("receipts/<str:pk>/",views.receipt_detail,name="receipt_detail"),
path("receipts/<str:pk>/print/",views.receipt_print,name="receipt_print"),
path("statements/",views.statement_list,name="statement_list"),path("statements/<str:student_pk>/",views.student_statement,name="student_statement"),]

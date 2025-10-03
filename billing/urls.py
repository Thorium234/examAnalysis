from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Invoice management
    path('', views.invoice_list, name='invoice_list'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<str:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<str:invoice_id>/pay/', views.pay_invoice, name='pay_invoice'),

    # Receipt management
    path('receipts/', views.receipt_list, name='receipt_list'),

    # Payment processing
    path('payment/process/', views.process_payment, name='process_payment'),

    # API endpoints for AJAX
    path('api/invoices/<str:invoice_id>/pay/', views.api_pay_invoice, name='api_pay_invoice'),
]
from django.contrib import admin
from .models import Subscription, Invoice, Receipt, Payment

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['school', 'subscription_type', 'amount', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'subscription_type']
    search_fields = ['school__name']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'school', 'gross_amount', 'balance_due', 'due_date', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['invoice_number', 'school__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'invoice', 'amount', 'date_paid', 'mode_of_payment', 'status']
    list_filter = ['status', 'mode_of_payment', 'date_paid']
    search_fields = ['receipt_number', 'invoice__invoice_number']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'date_paid', 'payment_type', 'status']
    list_filter = ['status', 'payment_type', 'date_paid']
    search_fields = ['student__name', 'student__admission_number']
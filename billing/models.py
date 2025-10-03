from django.db import models
from django.conf import settings
from school.models import School

class Subscription(models.Model):
    """School subscription model"""
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='subscription')
    subscription_type = models.CharField(max_length=50, choices=[
        ('ANNUAL', 'Annual'),
        ('MONTHLY', 'Monthly'),
    ], default='ANNUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ], default='ACTIVE')
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.subscription_type}"

class Invoice(models.Model):
    """Invoice model for billing"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    item_description = models.TextField()
    period_start = models.DateField()
    period_end = models.DateField()
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"INV{self.invoice_number} - {self.school.name}"

class Receipt(models.Model):
    """Payment receipt model"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='receipts')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()
    mode_of_payment = models.CharField(max_length=20, choices=[
        ('M_PESA', 'M-Pesa'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('CASH', 'Cash'),
    ])
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ], default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RCP{self.receipt_number or self.id} - {self.invoice.school.name}"

class Payment(models.Model):
    """Individual payment records"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=50, choices=[
        ('FEES', 'School Fees'),
        ('EXAM', 'Exam Fees'),
        ('OTHER', 'Other'),
    ], default='FEES')
    status = models.CharField(max_length=20, choices=[
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('UNPAID', 'Unpaid'),
    ], default='PAID')
    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.amount} ({self.date_paid})"
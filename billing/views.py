from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Invoice, Receipt, Subscription

@login_required
def invoice_list(request):
    """Display list of invoices for the user's school"""
    if not request.user.school:
        messages.error(request, "You must be associated with a school to view invoices.")
        return redirect('school:school_dashboard')

    # Get all invoices for the school
    invoices = Invoice.objects.filter(school=request.user.school).order_by('-created_at')

    # Calculate summary statistics
    total_balance = invoices.filter(status__in=['PENDING', 'OVERDUE']).aggregate(
        total=Sum('balance_due'))['total'] or 0

    unallocated_balance = 0  # This would be calculated based on payments not allocated to specific invoices

    context = {
        'invoices': invoices,
        'total_balance': total_balance,
        'unallocated_balance': unallocated_balance,
    }

    return render(request, 'billing/invoice_list.html', context)

@login_required
def invoice_detail(request, invoice_id):
    """Display detailed view of a specific invoice"""
    if not request.user.school:
        messages.error(request, "You must be associated with a school to view invoices.")
        return redirect('school:school_dashboard')

    invoice = get_object_or_404(
        Invoice,
        invoice_number=invoice_id,
        school=request.user.school
    )

    # Get related receipts
    receipts = Receipt.objects.filter(invoice=invoice).order_by('-date_paid')

    context = {
        'invoice': invoice,
        'receipts': receipts,
    }

    return render(request, 'billing/invoice_detail.html', context)

@login_required
def pay_invoice(request, invoice_id):
    """Display payment modal for an invoice"""
    if not request.user.school:
        messages.error(request, "You must be associated with a school to make payments.")
        return redirect('school:school_dashboard')

    invoice = get_object_or_404(
        Invoice,
        invoice_number=invoice_id,
        school=request.user.school
    )

    if request.method == 'POST':
        # Process payment (this would integrate with M-Pesa/Bank APIs)
        amount = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')

        # For now, just create a pending receipt
        receipt = Receipt.objects.create(
            invoice=invoice,
            amount=amount,
            date_paid=timezone.now().date(),
            mode_of_payment='M_PESA',
            phone_number=phone_number,
            status='PENDING'
        )

        messages.success(request, f"Payment request sent for KSH {amount}. Receipt: {receipt.receipt_number}")
        return redirect('billing:invoice_detail', invoice_id=invoice_id)

    context = {
        'invoice': invoice,
    }

    return render(request, 'billing/pay_invoice.html', context)

@login_required
def receipt_list(request):
    """Display list of receipts for the user's school"""
    if not request.user.school:
        messages.error(request, "You must be associated with a school to view receipts.")
        return redirect('school:school_dashboard')

    # Get all receipts for the school
    receipts = Receipt.objects.filter(
        invoice__school=request.user.school
    ).select_related('invoice').order_by('-date_paid')

    context = {
        'receipts': receipts,
    }

    return render(request, 'billing/receipt_list.html', context)

@login_required
def process_payment(request):
    """Process payment via AJAX (for future M-Pesa integration)"""
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')

        try:
            invoice = Invoice.objects.get(
                invoice_number=invoice_id,
                school=request.user.school
            )

            # Here you would integrate with M-Pesa API
            # For now, simulate successful payment
            receipt = Receipt.objects.create(
                invoice=invoice,
                amount=amount,
                date_paid=timezone.now().date(),
                mode_of_payment='M_PESA',
                phone_number=phone_number,
                status='COMPLETED',
                receipt_number=f"RCP{timezone.now().strftime('%Y%m%d%H%M%S')}"
            )

            # Update invoice balance
            invoice.balance_due -= float(amount)
            if invoice.balance_due <= 0:
                invoice.status = 'PAID'
                invoice.balance_due = 0
            invoice.save()

            return JsonResponse({
                'success': True,
                'message': f'Payment of KSH {amount} processed successfully.',
                'receipt_number': receipt.receipt_number
            })

        except Invoice.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invoice not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def api_pay_invoice(request, invoice_id):
    """API endpoint for payment processing"""
    return process_payment(request)
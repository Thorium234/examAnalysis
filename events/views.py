from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta
import calendar as cal
from django.utils import timezone
from .models import Event
from .forms import EventForm

@login_required
def calendar_view(request):
    # Get current month/year from GET params or use current date
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    view_type = request.GET.get('view', 'month')  # month, week, day, list

    # Create calendar
    cal_obj = cal.monthcalendar(year, month)
    month_name = cal.month_name[month]

    # Get events for this month
    start_date = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end_date = timezone.make_aware(datetime(year + 1, 1, 1))
    else:
        end_date = timezone.make_aware(datetime(year, month + 1, 1))

    events = Event.objects.filter(
        school=request.user.school,
        start_date__gte=start_date,
        start_date__lt=end_date
    )

    # Organize events by day
    events_by_day = {}
    for event in events:
        day = event.start_date.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    context = {
        'calendar': cal_obj,
        'year': year,
        'month': month,
        'month_name': month_name,
        'events_by_day': events_by_day,
        'view_type': view_type,
        'today': now,
    }

    return render(request, 'events/calendar.html', context)

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.school = request.user.school
            event.save()
            form.save_m2m()  # Save many-to-many relationships
            return JsonResponse({'success': True, 'message': 'Event created successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
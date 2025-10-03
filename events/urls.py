from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('create-event/', views.create_event, name='create_event'),
]
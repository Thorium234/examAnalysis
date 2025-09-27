from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.forms import inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Subject, SubjectPaper, SubjectCategory
from school.models import School

# Mixin to restrict views to school admins and HODs
class SchoolAdminOrHODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.profile.roles.filter(name__in=['School Admin', 'HOD']).exists()

class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.filter(school=self.request.user.school).order_by('name')

class SubjectCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = Subject
    template_name = 'subjects/subject_form.html'
    fields = ['name', 'code', 'category', 'is_optional']
    success_url = reverse_lazy('subjects:subject_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SubjectCategory.objects.filter(school=self.request.user.school)
        return context
    
    def form_valid(self, form):
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class SubjectUpdateView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = Subject
    template_name = 'subjects/subject_form.html'
    fields = ['name', 'code', 'category', 'is_optional']
    success_url = reverse_lazy('subjects:subject_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SubjectCategory.objects.filter(school=self.request.user.school)
        return context

    def get_queryset(self):
        return Subject.objects.filter(school=self.request.user.school)
    
class SubjectDeleteView(SchoolAdminOrHODRequiredMixin, DeleteView):
    model = Subject
    template_name = 'subjects/subject_confirm_delete.html'
    success_url = reverse_lazy('subjects:subject_list')
    
    def get_queryset(self):
        return Subject.objects.filter(school=self.request.user.school)

class SubjectPaperCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = SubjectPaper
    template_name = 'subjects/subject_paper_form.html'
    fields = ['subject', 'paper_number', 'max_marks', 'contribution_percentage']
    success_url = reverse_lazy('subjects:subject_list')

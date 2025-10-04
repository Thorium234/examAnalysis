from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count

from .models import Student, StudentAdvancement
from .forms import StudentForm
from school.models import School, FormLevel, Stream
from accounts.models import TeacherClass
from subjects.models import Subject, SubjectCategory


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.profile.roles.filter(name='Teacher').exists()


class StudentListView(TeacherRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 25

    def get_queryset(self):
        queryset = Student.objects.select_related('school', 'form_level')

        if not self.request.user.is_superuser:
            queryset = queryset.filter(school=self.request.user.school)

        # Filter by form level if provided
        form_level = self.request.GET.get('form_level')
        if form_level:
            queryset = queryset.filter(form_level=form_level)

        # Filter by stream if provided
        stream = self.request.GET.get('stream')
        if stream:
            queryset = queryset.filter(stream=stream)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(admission_number__icontains=search)
            )

        return queryset.order_by('admission_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_superuser:
            context['form_levels'] = FormLevel.objects.filter(school=self.request.user.school).annotate(student_count=Count('students'))
            context['streams'] = Stream.objects.filter(school=self.request.user.school)
        else:
            context['form_levels'] = FormLevel.objects.all().annotate(student_count=Count('students'))
            context['streams'] = Stream.objects.all()
        return context


class FormLevelDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = 'students/form_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level_id = self.kwargs['form_level']
        form_level = get_object_or_404(FormLevel, pk=form_level_id)

        if not self.request.user.is_superuser and form_level.school != self.request.user.school:
            raise PermissionError("You don't have access to this form level.")

        # Get students in this form level
        students = Student.objects.filter(form_level=form_level).select_related('school')

        # Group students by stream
        students_by_stream = {}
        for student in students:
            stream = student.stream or 'Unassigned'
            if stream not in students_by_stream:
                students_by_stream[stream] = []
            students_by_stream[stream].append(student)

        # Prepare stream data for template
        stream_data = []
        for stream_name, student_list in students_by_stream.items():
            stream_data.append({
                'stream': stream_name,
                'student_count': len(student_list),
            })

        # Get statistics
        total_students = students.count()
        streams_count = len(students_by_stream)

        context.update({
            'form_level': form_level,
            'students_by_stream': students_by_stream,
            'stream_data': stream_data,
            'students': students,
            'total_students': total_students,
            'streams_count': streams_count,
        })
        return context


class StreamStudentListView(TeacherRequiredMixin, ListView):
    model = Student
    template_name = 'students/stream_students.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        form_level_id = self.kwargs['form_level']
        stream_name = self.kwargs['stream']

        form_level = get_object_or_404(FormLevel, pk=form_level_id)

        if not self.request.user.is_superuser and form_level.school != self.request.user.school:
            raise PermissionError("You don't have access to this form level.")

        return Student.objects.filter(
            form_level=form_level,
            stream=stream_name
        ).order_by('admission_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level_id = self.kwargs['form_level']
        stream_name = self.kwargs['stream']
        form_level = get_object_or_404(FormLevel, pk=form_level_id)
        context['form_level'] = form_level
        context['stream'] = stream_name
        return context


class StudentCreateView(TeacherRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if not self.request.user.school and not self.request.user.is_superuser:
            form.add_error(None, "You must be associated with a school to create a student.")
            return self.form_invalid(form)

        if not self.request.user.is_superuser:
            form.instance.school = self.request.user.school

        messages.success(self.request, f"Student {form.instance.name} created successfully.")
        return super().form_valid(form)


class StudentUpdateView(TeacherRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Student.objects.all()
        return Student.objects.filter(school=self.request.user.school)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Student {form.instance.name} updated successfully.")
        return super().form_valid(form)


class StudentDeleteView(TeacherRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Student.objects.all()
        return Student.objects.filter(school=self.request.user.school)

    def delete(self, request, *args, **kwargs):
        student = self.get_object()
        messages.success(request, f"Student {student.name} deleted successfully.")
        return super().delete(request, *args, **kwargs)


class StudentSubjectEnrollmentView(TeacherRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_enrollment.html'
    fields = ['subjects']
    success_url = reverse_lazy('student_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Student.objects.all()
        return Student.objects.filter(school=self.request.user.school)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit subjects to those taught in the student's form level
        if self.object.form_level:
            from subjects.models import Subject
            form.fields['subjects'].queryset = Subject.objects.filter(
                form_levels=self.object.form_level
            )
        return form

    def form_valid(self, form):
        messages.success(self.request, f"Subjects updated for {self.object.name}.")
        return super().form_valid(form)


class StudentAdvancementCreateView(TeacherRequiredMixin, CreateView):
    model = StudentAdvancement
    template_name = 'students/advancement_form.html'
    fields = ['student', 'to_form_level', 'advancement_year']
    success_url = reverse_lazy('student_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            # Limit students to those in the user's school
            form.fields['student'].queryset = Student.objects.filter(school=self.request.user.school)
            # Limit form levels to those in the user's school
            form.fields['to_form_level'].queryset = FormLevel.objects.filter(school=self.request.user.school)
        return form

    def form_valid(self, form):
        student = form.cleaned_data['student']
        to_form_level = form.cleaned_data['to_form_level']

        # Set from_form_level automatically
        form.instance.from_form_level = student.form_level

        # Update student's form level
        student.form_level = to_form_level
        student.save()

        messages.success(self.request, f"Student {student.name} advanced to {to_form_level}.")
        return super().form_valid(form)


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Student.objects.all()
        return Student.objects.filter(school=self.request.user.school)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        # Get student's subjects
        context['student_subjects'] = student.subjects.all()

        # Get available subjects for the form level
        if student.form_level:
            from subjects.models import Subject
            context['available_subjects'] = Subject.objects.filter(form_levels=student.form_level)
        else:
            context['available_subjects'] = []

        # Get student's exam results (if any)
        from exams.models import ExamResult
        context['exam_results'] = ExamResult.objects.filter(student=student).select_related('exam', 'subject').order_by('-exam__year', '-exam__term')

        return context


class SubjectSelectionDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = 'students/subject_selection_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_superuser:
            context['form_levels'] = FormLevel.objects.filter(school=self.request.user.school).annotate(student_count=Count('students'))
        else:
            context['form_levels'] = FormLevel.objects.all().annotate(student_count=Count('students'))
        return context


class FormSubjectSelectionView(TeacherRequiredMixin, TemplateView):
    template_name = 'students/form_subject_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level_id = self.kwargs['form_level']
        form_level = get_object_or_404(FormLevel, pk=form_level_id)

        if not self.request.user.is_superuser and form_level.school != self.request.user.school:
            raise PermissionError("You don't have access to this form level.")

        context['form_level'] = form_level
        context['streams'] = Stream.objects.filter(form_level=form_level)
        return context


class StreamSubjectSelectionView(TeacherRequiredMixin, TemplateView):
    template_name = 'students/stream_subject_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level_id = self.kwargs['form_level']
        stream_name = self.kwargs['stream']
        form_level = get_object_or_404(FormLevel, pk=form_level_id)

        if not self.request.user.is_superuser and form_level.school != self.request.user.school:
            raise PermissionError("You don't have access to this form level.")

        context['form_level'] = form_level
        context['stream'] = stream_name

        # Get subjects by category
        subjects_by_category = {}
        for subject in Subject.objects.filter(school=form_level.school):
            category = subject.category.name if subject.category else 'Uncategorized'
            if category not in subjects_by_category:
                subjects_by_category[category] = []
            subjects_by_category[category].append(subject)

        context['subjects_by_category'] = subjects_by_category
        return context

    def post(self, request, *args, **kwargs):
        student = self.get_object()
        if 'subjects' in request.POST:
            subject_ids = request.POST.getlist('subjects')
            student.subjects.set(subject_ids)
            messages.success(request, f"Subjects updated for {student.name}.")
        return self.get(request, *args, **kwargs)
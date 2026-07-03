from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Department
from users.models import User

class DepartmentListView(LoginRequiredMixin, View):
    template_name = 'departments/list.html'

    def get(self, request):
        departments = Department.objects.select_related('head_of_department').all()
        # Fallback configuration parameter context
        users = User.objects.filter(role__in=['ADMIN', 'MANAGER'])
        return render(request, self.template_name, {'departments': departments, 'users': users})

class DepartmentCreateView(LoginRequiredMixin, View):
    def post(self, request):
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        hod_id = request.POST.get('head_of_department')
        dept_type = request.POST.get('type')

        if Department.objects.filter(code=code).exists():
            messages.error(request, f"Structural units error: Code mapping '{code}' collisions detected.")
            return redirect('department_list')

        hod_user = User.objects.filter(id=hod_id).first() if hod_id else None
        
        Department.objects.create(
            name=name,
            code=code.upper(),
            description=description,
            head_of_department=hod_user,
            type=dept_type
        )
        messages.success(request, f"Corporate department layer organizational structure node '{name}' mounted smoothly.")
        return redirect('department_list')
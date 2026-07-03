from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from users.models import User


class UserDirectoryListView(LoginRequiredMixin, View):

    template_name = "users/list.html"

    def get(self, request):

        users_query = User.objects.select_related(
            "department"
        ).order_by("-id")

        context = {

            "users_directory": users_query,

            "admin_count": users_query.filter(
                role="ADMIN"
            ).count(),

            "manager_count": users_query.filter(
                role="MANAGER"
            ).count(),

            "employee_count": users_query.filter(
                role="EMPLOYEE"
            ).count(),

        }

        return render(
            request,
            self.template_name,
            context
        )


class UserRoleUpdateGateway(LoginRequiredMixin, View):

    def post(self, request, user_id):

        target_user = get_object_or_404(
            User,
            id=user_id
        )

        new_role = request.POST.get("role")

        if new_role in User.Roles.values:

            target_user.role = new_role

            target_user.save()

            messages.success(
                request,
                f"{target_user.username}'s role updated successfully."
            )

        else:

            messages.error(
                request,
                "Invalid role selected."
            )

        return redirect("user_list")
    
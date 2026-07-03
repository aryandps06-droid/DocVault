from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth

from documents.models import Document
from departments.models import Department
from users.models import User


class LandingPageView(View):
    """Public-facing landing page. Redirect authenticated users to dashboard."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'core/landing.html')


class DashboardWorkspaceOverview(LoginRequiredMixin, View):

    template_name = "core/dashboard.html"

    def get(self, request):

        documents = Document.objects.select_related(
            "uploader",
            "department"
        )

        departments = Department.objects.annotate(
            doc_count=Count("documents")
        ).order_by("-doc_count")

        # Dashboard Cards
        total_documents = documents.count()
        total_departments = Department.objects.count()
        total_users = User.objects.count()

        approved_documents = documents.filter(
            ai_status="PROCESSED"
        ).count()

        pending_documents = documents.filter(
            ai_status="QUEUED"
        ).count()

        # Department Chart
        department_labels = []
        department_counts = []

        for dept in departments:

            department_labels.append(dept.name)
            department_counts.append(dept.doc_count)

        # Monthly Upload Chart
        monthly_uploads = (
            Document.objects
            .annotate(month=TruncMonth("uploaded_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        upload_labels = []
        upload_counts = []

        for item in monthly_uploads:

            upload_labels.append(
                item["month"].strftime("%b")
            )

            upload_counts.append(item["total"])

        context = {

            "total_documents": total_documents,

            "total_departments": total_departments,

            "total_users": total_users,

            "approved_documents": approved_documents,

            "pending_documents": pending_documents,

            "recent_documents_list": documents.order_by(
                "-uploaded_at"
            )[:6],

            "department_labels": department_labels,

            "department_counts": department_counts,

            "upload_labels": upload_labels,

            "upload_counts": upload_counts,

        }

        return render(
            request,
            self.template_name,
            context,
        )
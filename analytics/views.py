from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from documents.models import Document
from departments.models import Department
from users.models import User


class SystemTelemetrySummaryWorkspaceAnalyticsView(LoginRequiredMixin, View):
    template_name = "analytics/summary.html"

    def get(self, request):

        total_docs = Document.objects.count()

        processed_docs = Document.objects.filter(
            ai_status="PROCESSED"
        ).count()

        queued_docs = Document.objects.filter(
            ai_status="QUEUED"
        ).count()

        failed_docs = Document.objects.filter(
            ai_status="FAILED"
        ).count()

        department_stats = Department.objects.annotate(
            total_documents=Count("documents")
        ).order_by("-total_documents")

        active_user = (
            User.objects.annotate(
                total_uploads=Count("uploaded_docs")
            )
            .order_by("-total_uploads")
            .first()
        )

        context = {

            "total_docs_count": total_docs,

            "processed_docs_count": processed_docs,

            "queued_docs_count": queued_docs,

            "failed_docs_count": failed_docs,

            "structural_departments_count": Department.objects.count(),

            "total_users_count": User.objects.count(),

            "department_stats": department_stats,

            "active_user": active_user,

        }

        return render(
            request,
            self.template_name,
            context,
        )
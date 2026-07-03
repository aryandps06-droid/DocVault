from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Document
from departments.models import Department


class DocumentListView(LoginRequiredMixin, View):

    template_name = "documents/list.html"

    def get(self, request):

        documents = (
            Document.objects
            .select_related("uploader", "department")
            .order_by("-uploaded_at")
        )

        context = {
            "documents": documents,
            "departments": Department.objects.all(),
            "total_documents": documents.count(),
            "approved_documents": documents.filter(ai_status="PROCESSED").count(),
            "pending_documents": documents.exclude(ai_status="PROCESSED").count(),
        }

        return render(request, self.template_name, context)


class DocumentUploadGatewayView(LoginRequiredMixin, View):

    def post(self, request):

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:

            messages.error(request, "Please select a file to upload.")

            return redirect("document_list")

        title = request.POST.get("title")

        if not title:
            title = uploaded_file.name

        department_id = request.POST.get("department_id")
        assigned_department = request.user.department
        if department_id:
            try:
                assigned_department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass

        doc = Document.objects.create(
            title=title,
            file=uploaded_file,
            uploader=request.user,
            department=assigned_department,
            ai_status="QUEUED"
        )

        # ==========================================
        # REAL AI ENGINE PROCESSING
        # ==========================================
        from .utils import extract_text_from_file, generate_keywords, generate_abstract
        
        try:
            # Physically extract text from the saved file on disk
            extracted_text = extract_text_from_file(doc.file.path)
            
            if extracted_text:
                doc.extracted_raw_ocr_data = extracted_text
                doc.generated_summary_abstract = generate_abstract(extracted_text)
                doc.extracted_meta_keywords = generate_keywords(extracted_text)
                doc.ai_status = "PROCESSED"
                
                # We can still apply a basic heuristic for categorization if desired,
                # or rely on extracted keywords. We'll set a default for now.
                keywords_lower = [k.lower() for k in doc.extracted_meta_keywords]
                if "safety" in keywords_lower or "hazard" in keywords_lower:
                    doc.detected_category_tag = "Safety & Compliance"
                elif "mining" in keywords_lower or "coal" in keywords_lower:
                    doc.detected_category_tag = "Mining Operations"
                else:
                    doc.detected_category_tag = "General Document"
            else:
                doc.ai_status = "FAILED"
                doc.generated_summary_abstract = "No text could be extracted (likely an image or scanned document without OCR capabilities)."
                doc.detected_category_tag = "Requires Manual Review"
                
            doc.save()
        except Exception as e:
            print(f"AI Processing failed: {e}")
            doc.ai_status = "FAILED"
            doc.save()

        messages.success(
            request,
            "Document uploaded successfully."
        )

        return redirect("document_list")


class DocumentDetailWorkspaceOverview(LoginRequiredMixin, View):

    template_name = "documents/detail.html"

    def get(self, request, doc_id):

        document = get_object_or_404(Document, id=doc_id)

        return render(
            request,
            self.template_name,
            {
                "document": document
            }
        )


class DocumentDeleteView(LoginRequiredMixin, View):
    def get(self, request, doc_id):
        document = get_object_or_404(Document, id=doc_id)
        if request.user.is_superuser or document.uploader == request.user:
            document.delete()
            messages.success(request, f"Document '{document.title}' deleted successfully.")
        else:
            messages.error(request, "You do not have permission to delete this document.")
        return redirect('document_list')
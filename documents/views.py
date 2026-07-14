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

        import base64
        try:
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            file_base64_str = base64.b64encode(file_content).decode('utf-8')
        except Exception:
            file_base64_str = ""

        doc = Document.objects.create(
            title=title,
            file=uploaded_file,
            file_base64=file_base64_str,
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

        # Check if the file physically exists on the current serverless instance node, or we have the Base64 data in DB
        import os
        file_exists = False
        try:
            if (document.file and os.path.exists(document.file.path)) or document.file_base64:
                file_exists = True
        except Exception:
            pass

        return render(
            request,
            self.template_name,
            {
                "document": document,
                "file_exists": file_exists
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


class ServeDocumentView(LoginRequiredMixin, View):
    def get(self, request, doc_id):
        import base64
        import os
        from django.http import HttpResponse, Http404
        
        document = get_object_or_404(Document, id=doc_id)
        
        if not document.file_base64:
            # Fallback to local file if base64 data is not in DB
            if document.file and os.path.exists(document.file.path):
                with open(document.file.path, 'rb') as f:
                    file_data = f.read()
            else:
                raise Http404("Document file content not found.")
        else:
            try:
                file_data = base64.b64decode(document.file_base64)
            except Exception:
                raise Http404("Corrupted file data.")
                
        # Determine content type based on file name
        ext = os.path.splitext(document.file.name)[1].lower()
        if ext == '.pdf':
            content_type = 'application/pdf'
        elif ext in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif ext == '.png':
            content_type = 'image/png'
        elif ext == '.gif':
            content_type = 'image/gif'
        elif ext == '.webp':
            content_type = 'image/webp'
        else:
            content_type = 'application/octet-stream'
            
        response = HttpResponse(file_data, content_type=content_type)
        
        # Download or inline preview
        filename = document.file.name.split('/')[-1]
        if request.GET.get('download') == '1':
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
        return response
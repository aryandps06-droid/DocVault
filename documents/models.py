from django.db import models
from django.conf import settings

class Document(models.Model):
    class AIStatus(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued for Ingestion Processing Analysis'
        PROCESSED = 'PROCESSED', 'AI Parsing Diagnostics Pipelines Completed'
        FAILED = 'FAILED', 'Analysis Pipeline Breakdown Encountered'

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='secure_vault_repository/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_docs')
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    
    # Advanced AI Processing Pipeline Target Fields Map Matrix Metadata Records
    ai_status = models.CharField(max_length=20, choices=AIStatus.choices, default=AIStatus.QUEUED)
    extracted_raw_ocr_data = models.TextField(blank=True, null=True)
    generated_summary_abstract = models.TextField(blank=True, null=True)
    extracted_meta_keywords = models.JSONField(default=list, blank=True)
    detected_category_tag = models.CharField(max_length=100, blank=True, null=True)
    file_base64 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'kv_document_vault_ledger'

    def __str__(self):
        return f"{self.title} [Status: {self.ai_status}]"
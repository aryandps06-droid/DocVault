from documents.models import Document

def global_notifications(request):
    """
    Injects the latest 5 documents as system notifications into every template.
    """
    if request.user.is_authenticated:
        recent_docs = Document.objects.select_related('uploader').order_by('-uploaded_at')[:5]
        return {
            'global_notifications': recent_docs,
            'global_notif_count': recent_docs.count()
        }
    return {
        'global_notifications': [],
        'global_notif_count': 0
    }

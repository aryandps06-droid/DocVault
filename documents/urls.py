from django.urls import path
from . import views

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('upload/', views.DocumentUploadGatewayView.as_view(), name='document_upload'),
    path('detail/<int:doc_id>/', views.DocumentDetailWorkspaceOverview.as_view(), name='document_detail'),
    path('delete/<int:doc_id>/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('serve/<int:doc_id>/', views.ServeDocumentView.as_view(), name='document_serve'),
]
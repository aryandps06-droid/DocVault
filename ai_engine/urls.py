from django.urls import path
from . import views

urlpatterns = [
    path('trigger-pipeline/<int:doc_id>/', views.TriggerAIProcessingPipelineGateway.as_view(), name='trigger_ai_pipeline'),
]
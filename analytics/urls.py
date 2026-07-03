from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.SystemTelemetrySummaryWorkspaceAnalyticsView.as_view(), name='analytics_summary'),
]
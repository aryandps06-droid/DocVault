from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginWorkspaceView.as_view(), name='auth_login'),
    path('register/', views.RegisterWorkspaceView.as_view(), name='auth_register'),
    path('logout/', views.LogoutWorkspaceView.as_view(), name='auth_logout'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserDirectoryListView.as_view(), name='user_list'),
    path('role-update/<int:user_id>/', views.UserRoleUpdateGateway.as_view(), name='user_role_update'),
    path('delete/<int:user_id>/', views.UserDeleteView.as_view(), name='user_delete'),
]
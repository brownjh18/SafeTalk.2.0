from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_list_view, name='resource_list'),
    path('create/', views.resource_create_view, name='resource_create'),
    path('<int:resource_id>/', views.resource_detail_view, name='resource_detail'),
    path('<int:resource_id>/edit/', views.resource_edit_view, name='resource_edit'),
    path('<int:resource_id>/delete/', views.resource_delete_view, name='resource_delete'),
]
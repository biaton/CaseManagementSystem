from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list_view, name='list'),
    path('create/', views.create_announcement_view, name='create'),
    path('<int:pk>/edit/', views.edit_announcement_view, name='edit'),
    path('<int:pk>/delete/', views.delete_announcement_view, name='delete'),
]
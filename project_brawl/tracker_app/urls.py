# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('error/', views.error, name='error'),
    path('group-detail/<int:group_id>/', views.group_detail, name='group_detail'),
    path('create-group/', views.create_group, name='create_group'),
    path('add-player/<int:group_id>/', views.add_player, name='add_player'),
]

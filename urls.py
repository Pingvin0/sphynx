from django.contrib import admin
from django.urls import path
from . import views

app_name = "sphynx"

urlpatterns = [
    path('', views.index, name="index"),
    path('category/<int:id>/', views.category, name="category"),
    path('thread/<int:id>/', views.thread, name="thread"),
    path('new/<int:id>/', views.newThread, name="newthread"),
    path('profile/<int:id>/', views.profile, name="profile"),
    path('auth/', views.auth, name="auth"),
    path('login/', views.loginUser, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('comment/<int:id>/', views.comment, name="comment"),
    path('edit/<int:id>/', views.edit, name="edit"),
]


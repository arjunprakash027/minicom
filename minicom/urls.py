from django.urls import path
from minicom import views

urlpatterns = [
    path("login/", views.login_page),
    path("chat/", views.chat_user),
    path("admin/chat/", views.admin_list),
    path("admin/chat/<str:email>/", views.admin_chat),
]

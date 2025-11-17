"""djangotest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path

from minicom import api
from minicom import views

from django.urls import path


urlpatterns = [
    # Pages
    path('login/', views.login_page),
    path('chat/', views.chat_view),
    path('admin/chat/', views.admin_dashboard),
    path('admin/chat/<str:email>/', views.admin_chat_view),

    # API
    path('api/messages/<str:email>/', api.api_messages),
    path('api/send/<str:sender>/<str:receiver>/', api.api_send),
]


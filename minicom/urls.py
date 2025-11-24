# minicom/urls.py
from django.urls import path
from minicom import api

urlpatterns = [
    path('api/users/', api.list_users),
]

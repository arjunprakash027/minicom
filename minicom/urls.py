# minicom/urls.py
from django.urls import path
from minicom import api, views

urlpatterns = [
    path('api/users/', api.list_users),
]

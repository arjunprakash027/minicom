from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
import json

from .models import Message

def is_admin(request):
    """Check session state: is this the admin?"""
    return request.session.get("role") == "admin"

def is_user(request):
    """Check session state: is this a participant / customer?"""
    return request.session.get("role") == "user"

def get_user_email(request):
    """
    Only users have emails in session.
    Admin never has participant_email in session.
    """
    return request.session.get("email")

def login_page(request):
    return render(request, "login.html")

def chat_view(request):
    return render(request, "chat.html")

def admin_dashboard(request):
    """
    The admin home page.
    We hard-set admin identity in session (since there's only one admin).

    This page shows a list of participant emails derived from messages.
    """

    participants = (
        Message.objects
        .values_list("participant_email", flat=True)
        .distinct()
        .order_by("participant_email")
    )

    return render(request, "admin_list.html", {"participants": participants})


def admin_chat_view(request, email):
    """
    Admin opens a chat with a specific participant using email as key.
    """

    return render(request, "admin_chat.html", {"email": email})



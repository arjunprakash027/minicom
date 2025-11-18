from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
import json

from .models import Message


def login_page(request):
    return render(request, "login.html")

def chat_user(request):
    return render(request, "chat.html")

def admin_list(request):
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


def admin_chat(request, email):
    """
    Admin opens a chat with a specific participant using email as key.
    """

    return render(request, "admin_chat.html", {"email": email})



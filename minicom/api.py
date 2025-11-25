import json

from django.http import HttpResponse, JsonResponse

from .models import Message


def list_users(request):
    participants = (Message.objects.values_list(
        "participant_email",
        flat=True).distinct().order_by("participant_email"))
    return JsonResponse(list(participants), safe=False)
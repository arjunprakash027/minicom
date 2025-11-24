import json

from django.http import HttpResponse, JsonResponse

from .models import Message


def render_to_json(content, **kwargs):
    return HttpResponse(json.dumps(content),
                        content_type='application/json',
                        **kwargs)


def verify(request):
    return render_to_json({'success': True})


def list_users(request):
    participants = (Message.objects.values_list(
        "participant_email",
        flat=True).distinct().order_by("participant_email"))
    return JsonResponse(list(participants), safe=False)

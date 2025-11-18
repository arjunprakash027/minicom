import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from .models import Message
from django.http import HttpResponse

def render_to_json(content, **kwargs):
  return HttpResponse(json.dumps(content), content_type='application/json', **kwargs)

def verify(request):
  return render_to_json({'success': True})

def list_users(request):
    """
    Return a JSON array of participant emails (distinct).
    Used by the admin frontend to populate the sidebar.
    """
    participants = (
        Message.objects
        .values_list("participant_email", flat=True)
        .distinct()
        .order_by("participant_email")
    )
    # make simple list
    return JsonResponse(list(participants), safe=False)
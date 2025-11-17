import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from .models import Message
from django.http import HttpResponse

def render_to_json(content, **kwargs):
  return HttpResponse(json.dumps(content), content_type='application/json', **kwargs)

def verify(request):
  return render_to_json({'success': True})

def api_messages(request, email):

    messages = Message.objects.filter(participant_email=email)

    return JsonResponse([
        {"sender_type": m.sender_type, "content": m.content}
        for m in messages
    ], safe=False)

@csrf_exempt
def api_send(request, sender, receiver):
    data = json.loads(request.body.decode())
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "empty"}, status=400)
  
    if sender == 'admin@minicom.com':
        sender_type = "admin"
        partispant_email = receiver
    else:
       sender_type = "user"
       partispant_email = sender

    Message.objects.create(
        participant_email=partispant_email,
        sender_type=sender_type,
        content=content
    )

    return JsonResponse({"status": "ok"})
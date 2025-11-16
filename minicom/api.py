import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from .models import Message
from django.http import HttpResponse

def render_to_json(content, **kwargs):
  return HttpResponse(json.dumps(content), content_type='application/json', **kwargs)


def verify(request):
  return render_to_json({'success': True})

@csrf_exempt
def api_identify(request):
    data = json.loads(request.body.decode())
    email = data.get("email")
    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    request.session["email"] = email
    return JsonResponse({"status": "ok"})

def api_messages(request, email):
    user_email = request.session.get("email")

    # User can only access their own messages
    if user_email != email and not request.path.startswith("/admin/"):
        return HttpResponseForbidden("not allowed")

    messages = Message.objects.filter(participant_email=email)

    return JsonResponse([
        {"sender_type": m.sender_type, "content": m.content}
        for m in messages
    ], safe=False)

@csrf_exempt
def api_send(request, email):
    data = json.loads(request.body.decode())
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "empty"}, status=400)

    session_email = request.session.get("email")
    sender_type = "admin"
    if session_email == email:
        sender_type = "user"

    Message.objects.create(
        participant_email=email,
        sender_type=sender_type,
        content=content
    )

    return JsonResponse({"status": "ok"})
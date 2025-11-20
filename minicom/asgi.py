import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minicom.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from minicom.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
})

from django.urls import re_path
from message.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<chat_hash>[0-9a-f]+)/$", ChatConsumer.as_asgi()),
]

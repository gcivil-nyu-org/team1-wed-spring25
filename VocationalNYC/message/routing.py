from django.urls import path
from message.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<str:chat_hash>/", ChatConsumer.as_asgi()),
]

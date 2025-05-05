from django.urls import path
from message.consumers import ChatConsumer, ChatListConsumer

websocket_urlpatterns = [
    path("ws/chat/<str:chat_hash>/", ChatConsumer.as_asgi()),
    path("ws/chat_list/", ChatListConsumer.as_asgi()),
]

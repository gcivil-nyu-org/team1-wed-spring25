import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_hash = self.scope["url_route"]["kwargs"]["chat_hash"]
        self.room_group_name = f"chat_{self.chat_hash}"
        await self.accept()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get("message", "")
        sender_username = data.get("sender", "")
        if not message_content or not sender_username:
            return
        await self.save_message(message_content, sender_username)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_content,
                "sender": sender_username,
            },
        )
    
    @database_sync_to_async
    def save_message(self, message_content, sender_username):
        chat = Chat.objects.get(chat_hash=self.chat_hash)
        sender = User.objects.get(username=sender_username)
        recipient = chat.user2 if sender == chat.user1 else chat.user1
        
        Message.objects.create(
            chat=chat,
            sender=sender,
            recipient=recipient,
            content=message_content
        )
    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender": event["sender"],
                }
            )
        )

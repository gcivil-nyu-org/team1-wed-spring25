import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_hash = self.scope["url_route"]["kwargs"]["chat_hash"]
        self.room_group_name = f"chat_{self.chat_hash}"
        await self.accept()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.send(text_data=json.dumps({
            "type": "debug",
            "message": f"Connect to {self.room_group_name}"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_content = data.get("message", "")
            sender_username = data.get("sender", "")
            if not message_content or not sender_username:
                await self.send(
                    text_data=json.dumps({"error": "Missing message or sender"})
                )
                return
            await self.send(text_data=json.dumps({
                "type": "debug",
                "message": f"ECHO: {message_content}",
            }))
            # await self.send(
            #     text_data=json.dumps(
            #         {
            #             "message": f"ECHO: {message_content}",
            #             "sender": sender_username,
            #         }
            #     )
            # )
            message_id = await self.save_message(message_content, sender_username)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message_content,
                    "sender": sender_username,
                    "message_id": message_id,
                },
            )
        except Exception as e:
            import traceback

            print(f"Error in receive method: {str(e)}")
            print(traceback.format_exc())
            await self.send(text_data=json.dumps({"error": f"Server error: {str(e)}"}))

    @database_sync_to_async
    def save_message(self, message_content, sender_username):
        try:
            chat = Chat.objects.get(chat_hash=self.chat_hash)
            sender = User.objects.get(username=sender_username)
            recipient = chat.user2 if sender == chat.user1 else chat.user1

            message = Message.objects.create(
                chat=chat, sender=sender, recipient=recipient, content=message_content
            )

            channel_layer = get_channel_layer()
            timestamp = timezone.now().isoformat()

            for user in [chat.user1, chat.user2]:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_chat_list",
                    {
                        "type": "chat_list_update",
                        "data": {
                            "chat_hash": chat.chat_hash,
                            "timestamp": timestamp,
                            "last_message": message.content,
                            "sender_username": sender.username,
                            "sender_full_name": sender.get_full_name(),
                            "sender_role": sender.role,
                            "sender_display_name": (
                                sender.provider_profile.name
                                if sender.role == "training_provider"
                                and hasattr(sender, "provider_profile")
                                else sender.username
                            ),
                        },
                    },
                )
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise

        return message.pk

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender": event["sender"],
                    "message_id": event.get("message_id"),
                }
            )
        )


class ChatListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"user_{user.id}_chat_list"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_list_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

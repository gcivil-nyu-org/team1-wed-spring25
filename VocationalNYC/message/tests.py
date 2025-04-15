import hashlib
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Chat, Message

import socket

# Create your tests here.

User = get_user_model()


class ChatModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")

    def test_chat_hash_generation(self):
        chat = Chat.objects.create(user1=self.user1, user2=self.user2)
        sorted_ids = sorted([str(self.user1.id), str(self.user2.id)])
        expected_hash = hashlib.sha256("-".join(sorted_ids).encode("utf-8")).hexdigest()
        self.assertEqual(chat.chat_hash, expected_hash)

    def test_same_user_validation(self):
        chat = Chat(user1=self.user1, user2=self.user1)
        with self.assertRaises(ValidationError):
            chat.full_clean()


class MessageModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.chat = Chat.objects.create(user1=self.user1, user2=self.user2)

    def test_valid_message(self):
        message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            recipient=self.user2,
            content="Test message",
        )
        # full_clean should not raise any errors
        message.full_clean()
        self.assertEqual(message.content, "Test message")

    def test_invalid_message_sender(self):
        # Create a third user who is not part of the chat.
        user3 = User.objects.create_user(username="user3", password="pass123")
        message = Message(
            chat=self.chat, sender=user3, recipient=self.user2, content="Hi"
        )
        with self.assertRaises(ValidationError):
            message.full_clean()


class RedisConnectivityTest(TestCase):
    def test_channel_layer_connectivity(self):
        # Try to connect to Redis (host and port must match your settings)
        try:
            socket.create_connection(("localhost", 6379), timeout=1)
        except (socket.error, socket.timeout):
            self.skipTest("Redis is not running on localhost:6379")

        # If we reach here, Redis is up — continue with test
        channel_layer = get_channel_layer()
        try:
            async_to_sync(channel_layer.group_send)(
                "test_group", {"type": "test.message", "message": "hello"}
            )
        except Exception as e:
            self.fail(f"Channel layer (Redis) connectivity failed: {e}")

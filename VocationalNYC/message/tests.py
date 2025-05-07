import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Chat, Message, MessageVisibility
from users.models import Provider
from django.utils import timezone
from unittest.mock import patch, Mock, MagicMock
from message.views import create_message_with_visibility

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


class ChatViewsTest(TestCase):
    def setUp(self):
        # create test users
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="password123",
            role="career_changer",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="password123",
            role="training_provider",
        )

        # create a chat between user1 and user2
        self.chat = Chat.objects.create(user1=self.user1, user2=self.user2)

        # add messages to the chat
        self.message1 = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            recipient=self.user2,
            content="Test message 1",
            send_time=timezone.now(),
        )

        self.message2 = Message.objects.create(
            chat=self.chat,
            sender=self.user2,
            recipient=self.user1,
            content="Test message 2",
            send_time=timezone.now(),
        )

        # add provider information for user2
        self.provider = Provider.objects.create(
            user=self.user2,
            name="Test Provider",
            phone_num="1234567890",
            address="Test Address",
        )

    def test_chat_home_authenticated(self):
        """test authenticated user access to chat home"""
        self.client.login(username="testuser1", password="password123")
        response = self.client.get(reverse("chat_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat_ui.html")
        self.assertIn("chats", response.context)
        self.assertTrue(len(response.context["chats"]) > 0)

    def test_chat_home_unauthenticated(self):
        """test unauthenticated user access to chat home"""
        response = self.client.get(reverse("chat_home"))
        self.assertEqual(response.status_code, 302)  # should redirect to login
        self.assertTrue("/login/" in response.url)

    def test_chat_list_authenticated(self):
        """test authenticated user access to chat list"""
        self.client.login(username="testuser1", password="password123")
        response = self.client.get(reverse("chat_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat_list.html")
        self.assertIn("chats", response.context)
        self.assertEqual(len(response.context["chats"]), 1)  # should be one chat

    def test_chat_detail_authenticated_and_authorized(self):
        """test authenticated user access to chat detail"""
        self.client.login(username="testuser1", password="password123")
        response = self.client.get(
            reverse("chat_detail", kwargs={"chat_hash": self.chat.chat_hash})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat_ui.html")
        self.assertIn("messages", response.context)
        self.assertEqual(len(response.context["messages"]), 2)  # should be two messages

    def test_chat_detail_authenticated_but_unauthorized(self):
        """test logged in user access to chat detail without permission"""
        # create a new user and login
        User.objects.create_user(
            username="testuser3", email="test3@example.com", password="password123"
        )
        self.client.login(username="testuser3", password="password123")

        # try to access the chat detail page of user1 and user2's chat
        response = self.client.get(
            reverse("chat_detail", kwargs={"chat_hash": self.chat.chat_hash})
        )
        self.assertEqual(response.status_code, 403)  # should return forbidden

    def test_send_message(self):
        """Send a message and check if it is created correctly"""
        self.client.login(username="testuser1", password="password123")
        message_content = "New test message"

        # use a mock for the MessageForm to simulate form submission
        form_mock = Mock()
        form_mock.is_valid.return_value = True
        form_mock.cleaned_data = {"content": message_content}

        # mock the MessageForm and create_message_with_visibility function
        with patch("message.views.MessageForm", return_value=form_mock):
            with patch("message.views.create_message_with_visibility") as mock_create:
                response = self.client.post(
                    reverse("chat_detail", kwargs={"chat_hash": self.chat.chat_hash}),
                    {"content": message_content},
                )

                # verify the create_message_with_visibility function was called
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0]
                self.assertEqual(call_args[0], self.chat)
                self.assertEqual(call_args[1], self.user1)
                self.assertEqual(call_args[2], self.user2)
                self.assertEqual(call_args[3], message_content)

        # verify the message is created in the database
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("chat_detail", kwargs={"chat_hash": self.chat.chat_hash}),
        )

    def test_delete_message(self):
        """test deleting a message"""
        self.client.login(username="testuser1", password="password123")

        # delete the message
        response = self.client.post(
            reverse("delete_message", kwargs={"message_id": self.message1.id})
        )

        # should redirect to chat detail page
        self.assertEqual(response.status_code, 302)

        # verify the message is still in the database
        self.assertTrue(Message.objects.filter(id=self.message1.id).exists())

        # verify the message visibility is updated for the current user
        visibility = MessageVisibility.objects.get(
            user=self.user1, message=self.message1
        )
        self.assertFalse(visibility.is_visible)

        # verify the message visibility is still visible for the other user
        visibility = MessageVisibility.objects.get(
            user=self.user2, message=self.message1
        )
        self.assertTrue(visibility.is_visible)

    def test_delete_chat(self):
        """test deleting a chat"""
        self.client.login(username="testuser1", password="password123")

        # delete the chat
        response = self.client.post(
            reverse("delete_chat", kwargs={"chat_hash": self.chat.chat_hash})
        )

        # should redirect to chat list page
        self.assertEqual(response.status_code, 302)

        # verify the chat is still the database
        self.assertTrue(Chat.objects.filter(chat_hash=self.chat.chat_hash).exists())

        # verify the chat visibility is updated for the current user
        visibilities = MessageVisibility.objects.filter(
            user=self.user1, message__chat=self.chat
        )
        for visibility in visibilities:
            self.assertFalse(visibility.is_visible)

        # verify the chat visibility is still visible for the other user
        visibilities = MessageVisibility.objects.filter(
            user=self.user2, message__chat=self.chat
        )
        for visibility in visibilities:
            self.assertTrue(visibility.is_visible)

    def test_select_chat_partner_get(self):
        """test selecting a chat partner"""
        self.client.login(username="testuser1", password="password123")
        response = self.client.get(reverse("select_chat_partner"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/select_chat_partner.html")
        self.assertIn("users", response.context)

    def test_select_chat_partner_post_existing_chat(self):
        """test selecting an existing chat partner"""
        self.client.login(username="testuser1", password="password123")

        # select an existing chat partner
        response = self.client.post(
            reverse("select_chat_partner"), {"partner_id": self.user2.id}
        )

        # redirect to the existing chat detail page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("chat_detail", kwargs={"chat_hash": self.chat.chat_hash}),
        )

    def test_select_chat_partner_post_new_chat(self):
        """Test selecting a new chat partner"""
        # create a new user
        user3 = User.objects.create_user(
            username="testuser3", email="test3@example.com", password="password123"
        )

        self.client.login(username="testuser1", password="password123")

        # select the new chat partner
        response = self.client.post(
            reverse("select_chat_partner"), {"partner_id": user3.id}
        )

        # redirect to the new chat detail page
        self.assertEqual(response.status_code, 302)

        # verify the chat is created in the database
        chat = (
            Chat.objects.filter(user1=self.user1, user2=user3).first()
            or Chat.objects.filter(user1=user3, user2=self.user1).first()
        )

        self.assertIsNotNone(chat)
        self.assertEqual(
            response.url, reverse("chat_detail", kwargs={"chat_hash": chat.chat_hash})
        )

    def test_unauthorized_delete_message(self):
        """test unauthorized user deleting a message"""
        # create a new user and login
        User.objects.create_user(
            username="testuser3", email="test3@example.com", password="password123"
        )
        self.client.login(username="testuser3", password="password123")

        # try to delete a message that doesn't belong to the user
        response = self.client.post(
            reverse("delete_message", kwargs={"message_id": self.message1.id})
        )
        self.assertEqual(response.status_code, 403)  # should return forbidden

    def test_unauthorized_delete_chat(self):
        """test unauthorized user deleting a chat"""
        # create a new user and login
        User.objects.create_user(
            username="testuser3", email="test3@example.com", password="password123"
        )
        self.client.login(username="testuser3", password="password123")

        # try to delete a chat that doesn't belong to the user
        response = self.client.post(
            reverse("delete_chat", kwargs={"chat_hash": self.chat.chat_hash})
        )
        self.assertEqual(response.status_code, 403)  # should return forbidden


class CreateMessageWithVisibilityTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")

        # Create a test chat
        self.chat = Chat.objects.create(user1=self.user1, user2=self.user2)

    @patch("message.views.Message.objects.create")
    @patch("message.views.MessageVisibility.objects.create")
    def test_create_message_with_visibility(
        self, mock_visibility_create, mock_message_create
    ):
        """Test that create_message_with_visibility creates a message and visibility records"""
        # setup mock for Message.objects.create
        mock_message = MagicMock()
        mock_message.chat = self.chat
        mock_message.sender = self.user1
        mock_message.recipient = self.user2
        mock_message.content = "Test message"
        mock_message_create.return_value = mock_message

        before_call = timezone.now()
        # call the function to test
        create_message_with_visibility(
            self.chat, self.user1, self.user2, "Test message"
        )
        after_call = timezone.now()

        # verify Message.objects.create was called
        mock_message_create.assert_called_once()
        args, kwargs = mock_message_create.call_args

        self.assertEqual(kwargs["chat"], self.chat)
        self.assertEqual(kwargs["sender"], self.user1)
        self.assertEqual(kwargs["recipient"], self.user2)
        self.assertEqual(kwargs["content"], "Test message")

        # verify send_time is within the expected range
        self.assertTrue(hasattr(kwargs["send_time"], "year"))
        self.assertTrue(before_call <= kwargs["send_time"] <= after_call)

        # verify MessageVisibility.objects.create was called twice (once for each user)
        self.assertEqual(mock_visibility_create.call_count, 2)

        # verify fjrst call (for sender)
        mock_visibility_create.assert_any_call(
            user=self.user1, message=mock_message, is_visible=True
        )

        # verify second call (for recipient)
        mock_visibility_create.assert_any_call(
            user=self.user2, message=mock_message, is_visible=True
        )

    @patch("message.views.Message.objects.create")
    @patch("message.views.MessageVisibility.objects.create")
    def test_create_message_with_visibility_reverse_users(
        self, mock_visibility_create, mock_message_create
    ):
        """Test with user2 as sender and user1 as recipient"""
        # setup mock for Message.objects.create
        mock_message = MagicMock()
        mock_message.chat = self.chat
        mock_message.sender = self.user2
        mock_message.recipient = self.user1
        mock_message.content = "Reply message"
        mock_message_create.return_value = mock_message

        before_call = timezone.now()
        # call the function to test
        create_message_with_visibility(
            self.chat, self.user2, self.user1, "Reply message"
        )
        after_call = timezone.now()

        # verify Message.objects.create was called
        mock_message_create.assert_called_once()
        args, kwargs = mock_message_create.call_args

        self.assertEqual(kwargs["chat"], self.chat)
        self.assertEqual(kwargs["sender"], self.user2)
        self.assertEqual(kwargs["recipient"], self.user1)
        self.assertEqual(kwargs["content"], "Reply message")

        # verify send_time is within the expected range
        self.assertTrue(hasattr(kwargs["send_time"], "year"))
        self.assertTrue(before_call <= kwargs["send_time"] <= after_call)

        # verify MessageVisibility.objects.create was called twice (once for each user)
        self.assertEqual(mock_visibility_create.call_count, 2)

        # verify first call (for sender)
        mock_visibility_create.assert_any_call(
            user=self.user2, message=mock_message, is_visible=True
        )

        # verify second call (for recipient)
        mock_visibility_create.assert_any_call(
            user=self.user1, message=mock_message, is_visible=True
        )

    @patch("message.views.Message.objects.create")
    @patch("message.views.MessageVisibility.objects.create")
    def test_message_count_after_create(
        self, mock_visibility_create, mock_message_create
    ):
        """test the message count after creating messages"""
        # setup mock for Message.objects.create
        mock_message = MagicMock()
        mock_message_create.return_value = mock_message

        # create a message visibility record
        create_message_with_visibility(
            self.chat, self.user1, self.user2, "Test message for counting"
        )

        # verify Message.objects.create was called once
        self.assertEqual(mock_message_create.call_count, 1)

        # verify MessageVisibility.objects.create was called twice (once for each user)
        self.assertEqual(mock_visibility_create.call_count, 2)

from django.db import models
from django.contrib.auth import get_user_model
import hashlib
from django.core.exceptions import ValidationError

User = get_user_model()


class Chat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_user1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_user2")
    created_at = models.DateTimeField(auto_now_add=True)
    chat_hash = models.CharField(max_length=64, unique=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.user1 == self.user2:
            raise ValidationError("A chat must be between two distinct users.")

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1

        sorted_ids = sorted([str(self.user1.id), str(self.user2.id)])
        hash_input = "-".join(sorted_ids)
        self.chat_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    send_time = models.DateTimeField(auto_now_add=True)
    read_time = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.sender == self.recipient:
            raise ValidationError("Sender and recipient cannot be the same.")

        if self.sender not in [
            self.chat.user1,
            self.chat.user2,
        ] or self.recipient not in [self.chat.user1, self.chat.user2]:
            raise ValidationError(
                "Both sender and recipient must be participants of this chat."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Message {self.pk} from {self.sender.username} in Chat {self.chat.pk}"

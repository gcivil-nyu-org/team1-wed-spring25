from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
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
    send_time = models.DateTimeField(null=True, blank=True)
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
        is_new = self.pk is None
        self.full_clean()

        if is_new and not self.send_time:
            self.send_time = timezone.now()

        super().save(*args, **kwargs)

        if is_new:
            for user in (self.sender, self.recipient):
                MessageVisibility.objects.get_or_create(
                    user=user,
                    message=self,
                    defaults={"is_visible": True},
                )

    def __str__(self):
        return f"Message {self.pk} from {self.sender.username} in Chat {self.chat.pk}"


class MessageVisibility(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="visibilities"
    )
    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "message")

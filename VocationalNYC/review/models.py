from django.db import models
from django.conf import settings  # ✅ Import settings to get the custom user model
from courses.models import Course  # ✅ Import the Course model from courses app
from django.contrib.auth import get_user_model


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    content = models.TextField()
    score_rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment_url = models.CharField(max_length=255, blank=True, null=True)

    helpful_count = models.PositiveIntegerField(default=1)
    not_helpful_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Review {self.review_id} by {self.user.username} for {self.course.name}"


class ReviewReply(models.Model):
    reply_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    parent_reply = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_replies",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Reply {self.reply_id} to Review {self.review.review_id}"


User = get_user_model()


class ReviewVote(models.Model):
    review = models.ForeignKey("Review", on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(
        max_length=10, choices=[("upvote", "Upvote"), ("downvote", "Downvote")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("review", "user")

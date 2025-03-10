from django.db import models
from django.conf import settings  # ✅ Import settings to get the custom user model
from courses.models import Course  # ✅ Import the Course model from courses app


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )  # ✅ Use custom user model
    content = models.TextField()
    score_rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Review {self.review_id} by {self.user.username} for {self.course.name}"


class ReviewReply(models.Model):
    reply_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )  # ✅ Use custom user model
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

from django.db import models
from django.conf import settings
from courses.models import Course


class BookmarkList(models.Model):
    list_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmark_list"
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"bookmark list: {self.name}"

    class Meta:
        unique_together = ("user", "name")


class Bookmark(models.Model):
    bookmark_list = models.ForeignKey(
        BookmarkList, on_delete=models.CASCADE, related_name="bookmark"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="bookmark"
    )
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Course {self.course} in bookmark list {self.bookmark_list.list_id}"

    class Meta:
        unique_together = ("bookmark_list", "course")

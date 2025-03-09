from django.contrib import admin
from .models import Review, ReviewReply

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'user', 'course', 'score_rating', 'created_at')
    search_fields = ('user__username', 'content')

@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ('reply_id', 'user', 'review', 'parent_reply', 'created_at')
    search_fields = ('user__username', 'content')
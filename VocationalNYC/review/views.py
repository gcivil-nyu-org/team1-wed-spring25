from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from .models import Review, ReviewReply
from django.core.serializers import serialize

class ReviewListView(View):
    def get(self, request):
        reviews = Review.objects.all()
        data = serialize("json", reviews)
        return JsonResponse({'reviews': data}, safe=False)

class ReviewDetailView(View):
    def get(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        data = {
            'review_id': review.review_id,
            'user': review.user.username,
            'course': review.course_id,
            'content': review.content,
            'score_rating': review.score_rating,
            'created_at': review.created_at
        }
        return JsonResponse(data)

class ReviewReplyListView(View):
    def get(self, request):
        replies = ReviewReply.objects.all()
        data = serialize("json", replies)
        return JsonResponse({'replies': data}, safe=False)

class ReviewReplyDetailView(View):
    def get(self, request, pk):
        reply = get_object_or_404(ReviewReply, pk=pk)
        data = {
            'reply_id': reply.reply_id,
            'user': reply.user.username,
            'review': reply.review.review_id,
            'parent_reply': reply.parent_reply.reply_id if reply.parent_reply else None,
            'content': reply.content,
            'created_at': reply.created_at
        }
        return JsonResponse(data)

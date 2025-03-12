from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.serializers import serialize
from .models import ReviewReply
from .models import Review
from courses.models import Course

# from django.urls import reverse


class ReviewListView(View):
    def get(self, request):
        reviews = Review.objects.all()
        data = serialize("json", reviews)
        return JsonResponse({"reviews": data}, safe=False)


class ReviewDetailView(View):
    def get(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        data = {
            "review_id": review.review_id,
            "user": review.user.username,
            "course": review.course_id,
            "content": review.content,
            "score_rating": review.score_rating,
            "created_at": review.created_at,
        }
        return JsonResponse(data)


class ReviewReplyListView(View):
    def get(self, request):
        replies = ReviewReply.objects.all()
        data = serialize("json", replies)
        return JsonResponse({"replies": data}, safe=False)


class ReviewReplyDetailView(View):
    def get(self, request, pk):
        reply = get_object_or_404(ReviewReply, pk=pk)
        data = {
            "reply_id": reply.reply_id,
            "user": reply.user.username,
            "review": reply.review.review_id,
            "parent_reply": reply.parent_reply.reply_id if reply.parent_reply else None,
            "content": reply.content,
            "created_at": reply.created_at,
        }
        return JsonResponse(data)


@method_decorator(login_required, name="dispatch")
class ReviewCreateView(View):
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        content = request.POST.get("content")
        score_rating = request.POST.get("score_rating")

        if not content or not score_rating:
            return JsonResponse({"error": "All fields are required."}, status=400)

        Review.objects.create(
            course=course,
            user=request.user,
            content=content,
            score_rating=int(score_rating),
        )
        return redirect("course_detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReviewDeleteView(View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)

        if request.user != review.user:
            return JsonResponse(
                {"error": "You do not have permission to delete this review"},
                status=403,
            )

        # course_id = review.course.pk
        review.delete()
        return redirect("course_detail", pk=pk)

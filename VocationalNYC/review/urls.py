from django.urls import path
from .views import (
    ReviewListView,
    ReviewDetailView,
    ReviewReplyListView,
    ReviewReplyDetailView,
)

urlpatterns = [
    path("reviews/", ReviewListView.as_view(), name="review-list"),
    path("reviews/<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("replies/", ReviewReplyListView.as_view(), name="review-reply-list"),
    path(
        "replies/<int:pk>/", ReviewReplyDetailView.as_view(), name="review-reply-detail"
    ),
]

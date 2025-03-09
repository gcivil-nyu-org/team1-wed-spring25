from django.urls import path
from . import views
from .views import ReviewListView, ReviewDetailView, ReviewReplyListView, ReviewReplyDetailView, ReviewCreateView, ReviewDeleteView

urlpatterns = [
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('replies/', ReviewReplyListView.as_view(), name='review-reply-list'),
    path('replies/<int:pk>/', ReviewReplyDetailView.as_view(), name='review-reply-detail'),
    path('submit/<int:pk>/', ReviewCreateView.as_view(), name='review-create'),
    path('delete/<int:pk>/', ReviewDeleteView.as_view(), name='review-delete'),
]

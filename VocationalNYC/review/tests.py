from django.test import TestCase
from django.contrib.auth.models import User
from .models import Review, ReviewReply

class ReviewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.review = Review.objects.create(user=self.user, course_id=1, content="Great course!", score_rating=5)

    def test_review_creation(self):
        review = Review.objects.get(content="Great course!")
        self.assertEqual(review.score_rating, 5)

class ReviewReplyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.review = Review.objects.create(user=self.user, course_id=1, content="Great course!", score_rating=5)
        self.reply = ReviewReply.objects.create(user=self.user, review=self.review, content="I agree!")

    def test_review_reply_creation(self):
        reply = ReviewReply.objects.get(content="I agree!")
        self.assertEqual(reply.review, self.review)

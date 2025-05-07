from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Review, ReviewReply, ReviewVote
from courses.models import Course
from users.models import Provider

User = get_user_model()


class ReviewModelTests(TestCase):
    def setUp(self):
        # create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="career_changer",
        )

        # create a provider user
        self.provider_user = User.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="provider123",
            role="training_provider",
        )

        # create a provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            user=self.provider_user,
            phone_num="1234567890",
            address="123 Test St",
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user, course=self.course, content="Great course!", score_rating=5
        )

    def test_review_creation(self):
        """test review creation"""
        review = Review.objects.get(content="Great course!")
        self.assertEqual(review.score_rating, 5)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.course, self.course)

    def test_review_string_representation(self):
        """test review string representation"""
        expected_string = f"Review {self.review.review_id} by {self.user.username} for {self.course.name}"
        self.assertEqual(str(self.review), expected_string)

    def test_review_helpful_count(self):
        """test review helpful count initial value"""
        self.assertEqual(self.review.helpful_count, 0)

    def test_review_not_helpful_count(self):
        """test review not helpful count initial value"""
        self.assertEqual(self.review.not_helpful_count, 0)


class ReviewReplyModelTests(TestCase):
    def setUp(self):
        # create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="career_changer",
        )

        # create a provider user
        self.provider_user = User.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="provider123",
            role="training_provider",
        )

        # create a provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            user=self.provider_user,
            phone_num="1234567890",
            address="123 Test St",
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user, course=self.course, content="Great course!", score_rating=5
        )

        # create a reply
        self.reply = ReviewReply.objects.create(
            user=self.provider_user,
            review=self.review,
            content="Thank you for your feedback!",
        )

    def test_reply_creation(self):
        """test reply creation"""
        reply = ReviewReply.objects.get(content="Thank you for your feedback!")
        self.assertEqual(reply.review, self.review)
        self.assertEqual(reply.user, self.provider_user)

    def test_reply_string_representation(self):
        """test reply string representation"""
        expected_string = (
            f"Reply {self.reply.reply_id} to Review {self.review.review_id}"
        )
        self.assertEqual(str(self.reply), expected_string)

    def test_parent_reply_null(self):
        """test parent reply null"""
        self.assertIsNone(self.reply.parent_reply)

    def test_nested_reply(self):
        """test nested reply creation"""
        nested_reply = ReviewReply.objects.create(
            user=self.user,
            review=self.review,
            parent_reply=self.reply,
            content="Thanks for responding!",
        )
        self.assertEqual(nested_reply.parent_reply, self.reply)


class ReviewVoteModelTests(TestCase):
    def setUp(self):
        # test user
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            role="career_changer",
        )

        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
            role="career_changer",
        )

        # create a provider user
        self.provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890", address="123 Test St"
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user1, course=self.course, content="Great course!", score_rating=5
        )

    def test_upvote_creation(self):
        """test upvote creation"""
        vote = ReviewVote.objects.create(
            review=self.review, user=self.user2, action="upvote"
        )
        self.assertEqual(vote.action, "upvote")
        self.assertEqual(vote.user, self.user2)
        self.assertEqual(vote.review, self.review)

    def test_downvote_creation(self):
        """test downvote creation"""
        vote = ReviewVote.objects.create(
            review=self.review, user=self.user2, action="downvote"
        )
        self.assertEqual(vote.action, "downvote")

    def test_unique_user_review_constraint(self):
        """test unique user review constraint"""
        ReviewVote.objects.create(review=self.review, user=self.user2, action="upvote")
        # create a second vote for the same user and review should raise an exception
        with self.assertRaises(Exception):
            ReviewVote.objects.create(
                review=self.review, user=self.user2, action="downvote"
            )


class ReviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="career_changer",
        )

        # create a provider user
        self.provider_user = User.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="provider123",
            role="training_provider",
        )

        # create a provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            user=self.provider_user,
            phone_num="1234567890",
            address="123 Test St",
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user, course=self.course, content="Great course!", score_rating=5
        )

        # login test user
        self.client.login(username="testuser", password="password123")

    def test_review_list_view(self):
        """test review list view"""
        response = self.client.get(reverse("review-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("reviews", response.json())

    def test_review_detail_view(self):
        """test review detail view"""
        response = self.client.get(reverse("review-detail", args=[self.review.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "Great course!")

    def test_review_create_view(self):
        """test review create view"""
        # logout current user, login as another user
        self.client.logout()
        User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="newpass123",
            role="career_changer",
        )
        self.client.login(username="newuser", password="newpass123")

        data = {"content": "Another great course!", "score_rating": 4}
        response = self.client.post(
            reverse("review-create", args=[self.course.pk]), data
        )

        # should redirect to course detail page
        self.assertEqual(response.status_code, 302)

        # verify review created
        self.assertTrue(Review.objects.filter(content="Another great course!").exists())

    def test_review_delete_view(self):
        """test review delete view"""
        response = self.client.post(reverse("review-delete", args=[self.review.pk]))

        # should redirect to review list page
        self.assertEqual(response.status_code, 302)

        # verify review deleted
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_review_delete_unauthorized(self):
        """test review delete unauthorized access"""
        # logout current user, login as another user
        self.client.logout()
        User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpass123",
            role="career_changer",
        )
        self.client.login(username="otheruser", password="otherpass123")

        response = self.client.post(reverse("review-delete", args=[self.review.pk]))

        # should return 403 forbidden
        self.assertEqual(response.status_code, 403)

        # verify review still exists
        self.assertTrue(Review.objects.filter(pk=self.review.pk).exists())


class ReviewVoteViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="career_changer",
        )

        # create another test user for voting
        self.voter = User.objects.create_user(
            username="voter",
            email="voter@example.com",
            password="voter123",
            role="career_changer",
        )

        # create a provider user
        self.provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890", address="123 Test St"
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user, course=self.course, content="Great course!", score_rating=5
        )

        # login the voter user
        self.client.login(username="voter", password="voter123")

    def test_upvote_review(self):
        """test upvote review"""
        data = {"action": "upvote"}
        response = self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        self.assertEqual(response.status_code, 200)

        # refresh the review from the database
        self.review.refresh_from_db()

        # verify the vote count increased
        self.assertEqual(self.review.helpful_count, 1)
        self.assertEqual(self.review.not_helpful_count, 0)

    def test_downvote_review(self):
        """test downvote review"""
        data = {"action": "downvote"}
        response = self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        self.assertEqual(response.status_code, 200)

        # refresh the review from the database
        self.review.refresh_from_db()

        # verify the vote count increased
        self.assertEqual(self.review.helpful_count, 0)
        self.assertEqual(self.review.not_helpful_count, 1)

    def test_switch_vote(self):
        """test switch vote"""
        # upvote first
        data = {"action": "upvote"}
        self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        # then switch to downvote
        data = {"action": "downvote"}
        response = self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        self.assertEqual(response.status_code, 200)

        # refresh the review from the database
        self.review.refresh_from_db()

        # verify the vote count updated correctly
        self.assertEqual(self.review.helpful_count, 0)
        self.assertEqual(self.review.not_helpful_count, 1)

    def test_cancel_vote(self):
        """test cancel vote"""
        # upvote first
        data = {"action": "upvote"}
        self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        # upvote again to cancel
        response = self.client.post(reverse("review-vote", args=[self.review.pk]), data)

        self.assertEqual(response.status_code, 200)

        # refresh the review from the database
        self.review.refresh_from_db()

        # verify the vote count reset to zero
        self.assertEqual(self.review.helpful_count, 0)
        self.assertEqual(self.review.not_helpful_count, 0)


class ReviewReplyViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="career_changer",
        )

        # create a provider user
        self.provider_user = User.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="provider123",
            role="training_provider",
        )

        # create a provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            user=self.provider_user,
            phone_num="1234567890",
            address="123 Test St",
        )

        # create a course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            course_desc="Test course description",
            cost=1000,
            location="Test Location",
        )

        # create a review
        self.review = Review.objects.create(
            user=self.user, course=self.course, content="Great course!", score_rating=5
        )

    def test_reply_list_view(self):
        """test reply list view"""
        response = self.client.get(reverse("review-reply-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("replies", response.json())

    def test_provider_create_reply(self):
        """test provider create reply"""
        # login provider user
        self.client.login(username="provider", password="provider123")

        data = {"content": "Thank you for your feedback!"}
        response = self.client.post(
            reverse("review-reply-create", args=[self.review.pk]), data
        )

        # redirect to review detail page
        self.assertEqual(response.status_code, 302)

        # verify reply created
        self.assertTrue(
            ReviewReply.objects.filter(content="Thank you for your feedback!").exists()
        )

    def test_non_provider_create_reply(self):
        """test non-provider create reply"""
        # login test user
        self.client.login(username="testuser", password="password123")

        data = {"content": "This is my reply!"}
        response = self.client.post(
            reverse("review-reply-create", args=[self.review.pk]), data
        )

        # should return 403 forbidden
        self.assertEqual(response.status_code, 403)

        # verify reply not created
        self.assertFalse(
            ReviewReply.objects.filter(content="This is my reply!").exists()
        )

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationOtpTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse("register")
        self.verify_url = reverse("verify_email")
        self.login_url = reverse("login")
        self.payload = {
            "email": "signup@test.com",
            "password": "Test@Password#99!",
            "name": "Signup User",
            "birthdate": "01/01/2000",
        }

    @patch("user.views.send_otp", side_effect=Exception("SMTP rejected sender"))
    def test_register_rolls_back_when_otp_send_fails(self, mocked_send_otp):
        response = self.client.post(self.register_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(User.objects.filter(email=self.payload["email"]).exists())
        mocked_send_otp.assert_called_once()

    @patch("user.views.send_otp", return_value="123456")
    def test_register_creates_user_when_otp_send_succeeds(self, mocked_send_otp):
        response = self.client.post(self.register_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.payload["email"]).exists())
        mocked_send_otp.assert_called_once_with(
            self.payload["email"],
            "verify",
            "Verify your FitPro account",
        )

    def test_verify_email_marks_user_as_verified_and_login_then_succeeds(self):
        user = User.objects.create_user(
            email=self.payload["email"],
            password=self.payload["password"],
            username="signup_test",
            name=self.payload["name"],
            birthdate=self.payload["birthdate"],
        )
        cache.set(f"verify_{user.email}", "123456", timeout=600)

        verify_response = self.client.post(
            self.verify_url,
            {"email": user.email, "code": "123456"},
            format="json",
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        login_response = self.client.post(
            self.login_url,
            {"email": user.email, "password": self.payload["password"]},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)

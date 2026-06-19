from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import User


class UserProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            nickname="test-user",
            email="test@example.com",
            password="testpass1234",
        )


    def test_profile_api_requires_authentication(self):
        response = self.client.get(reverse("users:me-profile"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_get_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("users:me-profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["nickname"], "test-user")
        self.assertEqual(response.data["email"], "test@example.com")

    def test_authenticated_user_can_update_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("users:me-profile"),
            {
                "nickname": "updated-user",
                "profile_image_url": "https://example.com/profile.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "updated-user")
        self.assertEqual(
            response.data["profile_image_url"],
            "https://example.com/profile.jpg",
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "updated-user")

    def test_profile_api_does_not_allow_role_update(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("users:me-profile"),
            {
                "role": User.Role.ADMIN,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.USER)

class OAuthAuthorizationURLAPITests(APITestCase):
    @override_settings(
        OAUTH_PROVIDERS={
            "google": {
                "client_id": "google-client-id",
                "redirect_uri": "http://127.0.0.1:8000/api/v1/auth/oauth/google/callback/",
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "scope": "openid email profile",
                "extra_params": {
                    "access_type": "offline",
                    "prompt": "consent",
                },
            }
        }
    )
    def test_oauth_authorization_url_api_returns_authorization_url(self):
        response = self.client.get(reverse("auth:oauth-url", args=["google"]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["provider"], "google")
        self.assertIn(
            "https://accounts.google.com/o/oauth2/v2/auth?",
            response.data["authorization_url"],
        )
        self.assertIn("client_id=google-client-id", response.data["authorization_url"])
        self.assertIn("response_type=code", response.data["authorization_url"])

    def test_oauth_authorization_url_api_returns_404_for_unsupported_provider(self):
        response = self.client.get(reverse("auth:oauth-url", args=["github"]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Unsupported OAuth provider.")

    @override_settings(
        OAUTH_PROVIDERS={
            "google": {
                "client_id": "",
                "redirect_uri": "http://127.0.0.1:8000/api/v1/auth/oauth/google/callback/",
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "scope": "openid email profile",
                "extra_params": {},
            }
        }
    )
    def test_oauth_authorization_url_api_requires_client_id(self):
        response = self.client.get(reverse("auth:oauth-url", args=["google"]))

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data["detail"],
            "OAuth client_id is not configured.",
        )

class OAuthCallbackAPITests(APITestCase):
    @override_settings(
        OAUTH_PROVIDERS={
            "google": {
                "client_id": "google-client-id",
                "client_secret": "google-client-secret",
                "redirect_uri": "http://127.0.0.1:8000/api/v1/auth/oauth/google/callback/",
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
                "scope": "openid email profile",
                "extra_params": {},
            }
        }
    )
    @patch("apps.users.services.request_oauth_user_info")
    @patch("apps.users.services.request_oauth_access_token")
    def test_oauth_callback_creates_user_and_social_account(
        self,
        mock_request_oauth_access_token,
        mock_request_oauth_user_info,
    ):
        mock_request_oauth_access_token.return_value = "access-token"
        mock_request_oauth_user_info.return_value = {
            "sub": "google-user-id",
            "email": "google@example.com",
            "name": "Google User",
            "picture": "https://example.com/profile.jpg",
        }

        response = self.client.get(
            reverse("auth:oauth-callback", args=["google"]),
            {"code": "authorization-code"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["created"])
        self.assertEqual(response.data["user"]["email"], "google@example.com")
        self.assertEqual(response.data["user"]["nickname"], "Google User")

    def test_oauth_callback_requires_code(self):
        response = self.client.get(reverse("auth:oauth-callback", args=["google"]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "code query parameter is required.")

    def test_oauth_callback_returns_404_for_unsupported_provider(self):
        response = self.client.get(
            reverse("auth:oauth-callback", args=["github"]),
            {"code": "authorization-code"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Unsupported OAuth provider.")

class AuthSessionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sessionuser",
            nickname="session-user",
            email="session@example.com",
            password="testpass1234",
        )

    def test_session_api_returns_anonymous_state(self):
        response = self.client.get(reverse("auth:session"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["authenticated"])
        self.assertIsNone(response.data["user"])

    def test_session_api_returns_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("auth:session"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["authenticated"])
        self.assertEqual(response.data["user"]["id"], self.user.id)

    def test_logout_api_returns_204(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("auth:logout"))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
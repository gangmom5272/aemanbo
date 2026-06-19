from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            nickname="테스트유저",
            email="test@example.com",
            password="testpass1234",
        )


    def test_profile_api_requires_authentication(self):
        response = self.client.get(reverse("users:my-profile"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_get_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("users:my-profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["nickname"], "테스트유저")
        self.assertEqual(response.data["email"], "test@example.com")

    def test_authenticated_user_can_update_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("users:my-profile"),
            {
                "nickname": "수정된닉네임",
                "profile_image_url": "https://example.com/profile.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "수정된닉네임")
        self.assertEqual(
            response.data["profile_image_url"],
            "https://example.com/profile.jpg",
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "수정된닉네임")

    def test_profile_api_does_not_allow_role_update(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("users:my-profile"),
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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import login, logout

from .services import (
    MissingOAuthClientIDError,
    MissingOAuthClientSecretError,
    OAuthTokenRequestError,
    OAuthUserInfoRequestError,
    UnsupportedOAuthProviderError,
    authenticate_oauth_user,
    build_oauth_authorization_url,
)

from .serializers import UserProfileSerializer


class MyProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OAuthAuthorizationURLAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, provider):
        try:
            data = build_oauth_authorization_url(provider)
        except UnsupportedOAuthProviderError:
            return Response(
                {"detail": "Unsupported OAuth provider."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except MissingOAuthClientIDError:
            return Response(
                {"detail": "OAuth client_id is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(data)

class OAuthCallbackAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, provider):
        code = request.query_params.get("code")
        if not code:
            return Response(
                {"detail": "code query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user, created = authenticate_oauth_user(provider, code)
        except UnsupportedOAuthProviderError:
            return Response(
                {"detail": "Unsupported OAuth provider."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MissingOAuthClientIDError, MissingOAuthClientSecretError):
            return Response(
                {"detail": "OAuth client credentials are not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except OAuthTokenRequestError:
            return Response(
                {"detail": "Failed to request OAuth access token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OAuthUserInfoRequestError:
            return Response(
                {"detail": "Failed to request OAuth user info."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)

        return Response(
            {
                "created": created,
                "user": UserProfileSerializer(user).data,
            }
        )

class AuthSessionAPIView(APIView):
    # 세션 인증을 사용해야 로그인 상태(request.user)를 읽을 수 있음
    permission_classes = []

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {
                    "authenticated": False,
                    "user": None,
                }
            )

        return Response(
            {
                "authenticated": True,
                "user": UserProfileSerializer(request.user).data,
            }
        )


class LogoutAPIView(APIView):
    # 세션만 비우면 되므로 인증/CSRF 불필요
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


import os

from django.conf import settings as dj_settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.parsers import FormParser, MultiPartParser


@ensure_csrf_cookie
def csrf_view(request):
    # 프론트가 한 번 호출하면 csrftoken 쿠키가 설정됨 (이후 POST/PATCH에 사용)
    return JsonResponse({"detail": "CSRF cookie set"})


class AvatarUploadAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    ALLOWED = (".png", ".jpg", ".jpeg", ".gif", ".webp")

    def post(self, request):
        f = request.FILES.get("image")
        if not f:
            return Response(
                {"detail": "image file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in self.ALLOWED:
            return Response(
                {"detail": "unsupported file type."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if f.size > 5 * 1024 * 1024:
            return Response(
                {"detail": "file too large (max 5MB)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        path = f"avatars/user_{request.user.id}{ext}"
        if default_storage.exists(path):
            default_storage.delete(path)
        saved = default_storage.save(path, f)
        url = request.build_absolute_uri(dj_settings.MEDIA_URL + saved)

        request.user.profile_image_url = url
        request.user.save(update_fields=["profile_image_url"])
        return Response({"profile_image_url": url})

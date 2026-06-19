from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .services import (
    MissingOAuthClientIDError,
    MissingOAuthClientSecretError,
    OAuthTokenRequestError,
    OAuthUserInfoRequestError,
    UnsupportedOAuthProviderError,
    authenticate_oauth_user,
    build_oauth_authorization_url,
)

from django.contrib.auth import login, logout

from .serializers import UserProfileSerializer


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
    authentication_classes = []
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
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
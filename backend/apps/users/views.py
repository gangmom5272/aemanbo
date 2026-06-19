from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .services import (
    MissingOAuthClientIDError,
    UnsupportedOAuthProviderError,
    build_oauth_authorization_url,
)

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
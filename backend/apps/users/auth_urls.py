from django.urls import path

from .views import (
    AuthSessionAPIView,
    LogoutAPIView,
    OAuthAuthorizationURLAPIView,
    OAuthCallbackAPIView,
)

app_name = "auth"

urlpatterns = [
    path("session/", AuthSessionAPIView.as_view(), name="session"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path(
        "oauth/<str:provider>/url/",
        OAuthAuthorizationURLAPIView.as_view(),
        name="oauth-url",
    ),
    path(
        "oauth/<str:provider>/callback/",
        OAuthCallbackAPIView.as_view(),
        name="oauth-callback",
    ),
]
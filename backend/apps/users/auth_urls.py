from django.urls import path

from .views import OAuthAuthorizationURLAPIView, OAuthCallbackAPIView

app_name = "auth"

urlpatterns = [
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
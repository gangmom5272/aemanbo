from django.urls import path

from .views import OAuthAuthorizationURLAPIView

app_name = "auth"

urlpatterns = [
    path(
        "oauth/<str:provider>/url/",
        OAuthAuthorizationURLAPIView.as_view(),
        name="oauth-url",
    ),
]
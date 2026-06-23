from django.urls import path

from .views import AvatarUploadAPIView, MyProfileAPIView

app_name = "users"

urlpatterns = [
    path("me/profile/", MyProfileAPIView.as_view(), name="me-profile"),
    path("me/avatar/", AvatarUploadAPIView.as_view(), name="me-avatar"),
]

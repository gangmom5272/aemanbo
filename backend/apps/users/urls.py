from django.urls import path

from .views import MyProfileAPIView

app_name = "users"

urlpatterns = [
    path("me/profile/", MyProfileAPIView.as_view(), name="me-profile"),
]

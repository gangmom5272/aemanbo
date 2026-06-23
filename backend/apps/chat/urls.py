from django.urls import path

from .views import ChatMessageAPIView, ChatSessionAPIView

app_name = "chat"

urlpatterns = [
    path("chat/message/", ChatMessageAPIView.as_view(), name="chat-message"),
    path("chat/session/", ChatSessionAPIView.as_view(), name="chat-session"),
]

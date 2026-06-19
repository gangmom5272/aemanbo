from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "nickname",
            "profile_image_url",
            "role",
            "status",
            "joined_at",
        )
        read_only_fields = ("id", "username", "email", "role", "status", "joined_at")

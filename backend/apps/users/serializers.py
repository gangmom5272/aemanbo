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
            "preferred_genres",
            "onboarded",
        )
        read_only_fields = ("id", "username", "email", "role", "status", "joined_at")

    def validate_preferred_genres(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("리스트 형식이어야 합니다.")
        cleaned = []
        for v in value:
            if isinstance(v, str) and v.strip():
                v = v.strip()
                if v not in cleaned:
                    cleaned.append(v)
        return cleaned[:10]

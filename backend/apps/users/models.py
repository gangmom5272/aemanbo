from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "USER", "User"
        ADMIN = "ADMIN", "Admin"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DELETED = "DELETED", "Deleted"
        BANNED = "BANNED", "Banned"

    nickname = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    profile_image_url = models.URLField(max_length=500, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    joined_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nickname or self.username


class SocialAccount(models.Model):
    class Provider(models.TextChoices):
        KAKAO = "KAKAO", "Kakao"
        NAVER = "NAVER", "Naver"
        GOOGLE = "GOOGLE", "Google"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="unique_social_provider_user",
            )
        ]

    def __str__(self):
        return f"{self.provider} - {self.provider_user_id}"

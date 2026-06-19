from django.conf import settings
from django.db import models

from apps.works.models import Anime, Manga


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Favorite(TimeStampedModel):
    class TargetType(models.TextChoices):
        ANIME = "ANIME", "Anime"
        MANGA = "MANGA", "Manga"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    target_type = models.CharField(max_length=20, choices=TargetType.choices)
    target_id = models.PositiveBigIntegerField()
    status_label = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"],
                name="unique_user_favorite_target",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.target_type}:{self.target_id}"


class CommentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    DELETED = "DELETED", "Deleted"


class AnimeComment(TimeStampedModel):
    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="anime_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=CommentStatus.choices,
        default=CommentStatus.ACTIVE,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.anime.title} - {self.user}"


class MangaComment(TimeStampedModel):
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manga_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=CommentStatus.choices,
        default=CommentStatus.ACTIVE,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.manga.title} - {self.user}"

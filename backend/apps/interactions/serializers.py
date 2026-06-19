from rest_framework import serializers

from apps.works.models import Anime, Manga
from apps.works.serializers import AnimeSummarySerializer, MangaSummarySerializer

from .models import AnimeComment, CommentStatus, Favorite, MangaComment


class FavoriteSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = (
            "id",
            "target_type",
            "target_id",
            "status_label",
            "target",
            "created_at",
        )
        read_only_fields = ("id", "target", "created_at")

    def get_target(self, obj):
        if obj.target_type == Favorite.TargetType.ANIME:
            anime = Anime.objects.filter(id=obj.target_id).first()
            return AnimeSummarySerializer(anime).data if anime else None
        if obj.target_type == Favorite.TargetType.MANGA:
            manga = Manga.objects.filter(id=obj.target_id).first()
            return MangaSummarySerializer(manga).data if manga else None
        return None


class FavoriteCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Favorite.TargetType.choices)
    target_id = serializers.IntegerField(min_value=1)
    status_label = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
    )


class CommentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class BaseCommentSerializer(serializers.ModelSerializer):
    user = CommentUserSerializer(read_only=True)
    is_deleted = serializers.SerializerMethodField()

    class Meta:
        fields = (
            "id",
            "user",
            "parent",
            "content",
            "status",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "status",
            "is_deleted",
            "created_at",
            "updated_at",
        )

    def get_is_deleted(self, obj):
        return obj.status == CommentStatus.DELETED


class AnimeCommentSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        model = AnimeComment


class MangaCommentSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        model = MangaComment


class MyCommentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    target_type = serializers.CharField()
    target_id = serializers.IntegerField()
    target_title = serializers.CharField()
    content = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()

from rest_framework import serializers

from .models import Anime, AnimeMangaMapping, Manga, MetadataTag


class MetadataTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataTag
        fields = ("id", "name", "type")


class AnimeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Anime
        fields = (
            "id",
            "title",
            "poster_image_url",
            "status",
            "release_year",
        )


class AnimeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anime
        fields = (
            "id",
            "title",
            "poster_image_url",
            "release_year",
            "status",
            "rating_avg",
            "favorite_count",
        )


class MangaSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Manga
        fields = (
            "id",
            "title",
            "cover_image_url",
            "status",
        )


class MangaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manga
        fields = (
            "id",
            "title",
            "cover_image_url",
            "status",
            "rating_avg",
            "favorite_count",
        )


class AnimeDetailSerializer(serializers.ModelSerializer):
    tags = MetadataTagSerializer(many=True, read_only=True)

    class Meta:
        model = Anime
        fields = (
            "id",
            "title",
            "original_title",
            "poster_image_url",
            "banner_image_url",
            "type",
            "release_year",
            "episode_count",
            "status",
            "studio",
            "synopsis",
            "rating_avg",
            "rating_count",
            "favorite_count",
            "tags",
        )


class MangaDetailSerializer(serializers.ModelSerializer):
    tags = MetadataTagSerializer(many=True, read_only=True)

    class Meta:
        model = Manga
        fields = (
            "id",
            "title",
            "original_title",
            "cover_image_url",
            "banner_image_url",
            "author",
            "illustrator",
            "publisher",
            "description",
            "status",
            "rating_avg",
            "rating_count",
            "favorite_count",
            "tags",
        )


class AnimeMangaMappingSerializer(serializers.ModelSerializer):
    anime = AnimeSummarySerializer(read_only=True)
    manga = MangaSummarySerializer(read_only=True)

    class Meta:
        model = AnimeMangaMapping
        fields = (
            "id",
            "anime_season_label",
            "anime_episode_from",
            "anime_episode_to",
            "manga_volume_from",
            "manga_volume_to",
            "manga_chapter_from",
            "manga_chapter_to",
            "continue_volume",
            "continue_chapter",
            "mapping_text",
            "description",
            "anime",
            "manga",
        )


class MappingCardSerializer(serializers.ModelSerializer):
    anime = AnimeListSerializer(read_only=True)
    manga = MangaListSerializer(read_only=True)

    class Meta:
        model = AnimeMangaMapping
        fields = (
            "id",
            "mapping_text",
            "continue_volume",
            "continue_chapter",
            "anime",
            "manga",
        )


class MappingSearchResultSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source="anime.title", read_only=True)
    manga_title = serializers.CharField(source="manga.title", read_only=True)

    class Meta:
        model = AnimeMangaMapping
        fields = (
            "id",
            "mapping_text",
            "anime_title",
            "manga_title",
        )

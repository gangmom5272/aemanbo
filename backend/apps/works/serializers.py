from rest_framework import serializers

from .models import Anime, AnimeMangaMapping, Manga, MetadataTag


# AniList 장르 영문 → 한글 표기
GENRE_KO = {
    "Action": "액션",
    "Adventure": "모험",
    "Comedy": "코미디",
    "Drama": "드라마",
    "Ecchi": "에치",
    "Fantasy": "판타지",
    "Hentai": "성인",
    "Horror": "공포",
    "Mahou Shoujo": "마법소녀",
    "Mecha": "메카",
    "Music": "음악",
    "Mystery": "미스터리",
    "Psychological": "심리",
    "Romance": "로맨스",
    "Sci-Fi": "SF",
    "Slice of Life": "일상",
    "Sports": "스포츠",
    "Supernatural": "초자연",
    "Thriller": "스릴러",
}


def to_korean_genre(name):
    """장르명은 한글로 변환, 매핑에 없으면(스튜디오/기타 태그) 원문 유지."""
    return GENRE_KO.get(name, name)


class MetadataTagSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = MetadataTag
        fields = ("id", "name", "type")

    def get_name(self, obj):
        return to_korean_genre(obj.name)


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
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        genres = [t for t in obj.tags.all() if t.type == MetadataTag.TagType.GENRE]
        return MetadataTagSerializer(genres, many=True).data

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
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        genres = [t for t in obj.tags.all() if t.type == MetadataTag.TagType.GENRE]
        return MetadataTagSerializer(genres, many=True).data

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

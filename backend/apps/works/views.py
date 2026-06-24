from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Anime, AnimeMangaMapping, Manga
from .serializers import (
    AnimeDetailSerializer,
    AnimeListSerializer,
    AnimeMangaMappingSerializer,
    MangaListSerializer,
    MangaDetailSerializer,
    MappingCardSerializer,
    MappingSearchResultSerializer,
)
from .services import get_home_data, get_recommended_mappings, search_works


def _is_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (getattr(user, "role", "") == "ADMIN" or user.is_superuser)
    )


class GenreListAPIView(APIView):
    def get(self, request):
        # 설문/프로필 편집용 장르 목록 (영문 value + 한글 label)
        from .serializers import GENRE_KO

        genres = [{"value": en, "label": ko} for en, ko in GENRE_KO.items()]
        genres.sort(key=lambda g: g["label"])
        return Response({"results": genres})


class HomeAPIView(APIView):
    def get(self, request):
        home_data = get_home_data(user=request.user)

        return Response(
            {
                "recommended_mappings": MappingCardSerializer(
                    home_data["recommended_mappings"],
                    many=True,
                ).data,
                "popular_animes": AnimeListSerializer(
                    home_data["popular_animes"],
                    many=True,
                ).data,
                "popular_mangas": MangaListSerializer(
                    home_data["popular_mangas"],
                    many=True,
                ).data,
            }
        )


class SearchAPIView(APIView):
    def get(self, request):
        keyword = request.query_params.get("keyword", "")

        try:
            results = search_works(keyword)
        except ValueError:
            return Response(
                {"detail": "keyword query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "keyword": results["keyword"],
                "animes": AnimeListSerializer(results["animes"], many=True).data,
                "mangas": MangaListSerializer(results["mangas"], many=True).data,
                "mappings": MappingSearchResultSerializer(
                    results["mappings"],
                    many=True,
                ).data,
            }
        )


class MappingRecommendationsAPIView(APIView):
    def get(self, request):
        limit_param = request.query_params.get("limit")
        limit = 20

        if limit_param:
            try:
                limit = int(limit_param)
            except ValueError:
                return Response(
                    {"detail": "limit must be a number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        mappings = get_recommended_mappings(limit=limit)
        serializer = MappingCardSerializer(mappings, many=True)

        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            }
        )


class AnimeDetailAPIView(APIView):
    def get(self, request, anime_id):
        try:
            anime = Anime.objects.prefetch_related("tags").get(id=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {"detail": "Anime not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AnimeDetailSerializer(anime)
        return Response(serializer.data)

    def patch(self, request, anime_id):
        # 관리자만 제목/원제/줄거리 수정
        if not _is_admin(request.user):
            return Response({"detail": "관리자만 수정할 수 있어요."}, status=status.HTTP_403_FORBIDDEN)
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({"detail": "Anime not found."}, status=status.HTTP_404_NOT_FOUND)

        if "title" in request.data and not str(request.data.get("title") or "").strip():
            return Response({"detail": "제목은 비울 수 없어요."}, status=status.HTTP_400_BAD_REQUEST)
        for f in ("title", "original_title", "synopsis"):
            if f in request.data:
                setattr(anime, f, str(request.data.get(f) or "").strip())
        anime.save()
        return Response(AnimeDetailSerializer(anime).data)


class AnimeMangaMappingsAPIView(APIView):
    def get(self, request, anime_id):
        if not Anime.objects.filter(id=anime_id).exists():
            return Response(
                {"detail": "Anime not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        mappings = (
            AnimeMangaMapping.objects.select_related("anime", "manga")
            .filter(anime_id=anime_id)
            .order_by("anime_episode_from", "id")
        )
        serializer = AnimeMangaMappingSerializer(mappings, many=True)

        return Response(
            {
                "anime_id": anime_id,
                "mappings": serializer.data,
            }
        )


class MangaDetailAPIView(APIView):
    def get(self, request, manga_id):
        try:
            manga = Manga.objects.prefetch_related("tags").get(id=manga_id)
        except Manga.DoesNotExist:
            return Response(
                {"detail": "Manga not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MangaDetailSerializer(manga)
        return Response(serializer.data)

    def patch(self, request, manga_id):
        # 관리자만 제목/원제/줄거리 수정
        if not _is_admin(request.user):
            return Response({"detail": "관리자만 수정할 수 있어요."}, status=status.HTTP_403_FORBIDDEN)
        try:
            manga = Manga.objects.get(id=manga_id)
        except Manga.DoesNotExist:
            return Response({"detail": "Manga not found."}, status=status.HTTP_404_NOT_FOUND)

        if "title" in request.data and not str(request.data.get("title") or "").strip():
            return Response({"detail": "제목은 비울 수 없어요."}, status=status.HTTP_400_BAD_REQUEST)
        for f in ("title", "original_title", "description"):
            if f in request.data:
                setattr(manga, f, str(request.data.get(f) or "").strip())
        manga.save()
        return Response(MangaDetailSerializer(manga).data)


class MangaAnimeMappingsAPIView(APIView):
    def get(self, request, manga_id):
        if not Manga.objects.filter(id=manga_id).exists():
            return Response(
                {"detail": "Manga not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        mappings = (
            AnimeMangaMapping.objects.select_related("anime", "manga")
            .filter(manga_id=manga_id)
            .order_by("anime_id", "anime_episode_from", "id")
        )
        serializer = AnimeMangaMappingSerializer(mappings, many=True)

        return Response(
            {
                "manga_id": manga_id,
                "mappings": serializer.data,
            }
        )


class AnimeListAPIView(APIView):
    def get(self, request):
        queryset = Anime.objects.all()
        genre = request.query_params.get("genre")
        if genre and genre != "전체":
            queryset = queryset.filter(tags__name=genre)
        sort = request.query_params.get("sort", "name")
        ordering = {
            "name": "title",
            "pop": "-favorite_count",
            "recent": "-release_year",
            "rating": "-rating_avg",
        }.get(sort, "title")
        queryset = queryset.order_by(ordering, "title").distinct()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(60, max(1, int(request.query_params.get("page_size", 24))))
        except (TypeError, ValueError):
            page_size = 24

        total = queryset.count()
        start = (page - 1) * page_size
        items = queryset[start:start + page_size]
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "results": AnimeListSerializer(items, many=True).data,
            }
        )


class MangaListAPIView(APIView):
    def get(self, request):
        queryset = Manga.objects.all()
        genre = request.query_params.get("genre")
        if genre and genre != "전체":
            queryset = queryset.filter(tags__name=genre)
        sort = request.query_params.get("sort", "name")
        ordering = {
            "name": "title",
            "pop": "-favorite_count",
            "recent": "-created_at",
            "rating": "-rating_avg",
        }.get(sort, "title")
        queryset = queryset.order_by(ordering, "title").distinct()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(60, max(1, int(request.query_params.get("page_size", 24))))
        except (TypeError, ValueError):
            page_size = 24

        total = queryset.count()
        start = (page - 1) * page_size
        items = queryset[start:start + page_size]
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "results": MangaListSerializer(items, many=True).data,
            }
        )

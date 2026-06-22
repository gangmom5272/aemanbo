from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Anime, AnimeMangaMapping, Manga, MangaEpisode
from .serializers import (
    AnimeDetailSerializer,
    AnimeListSerializer,
    AnimeMangaMappingSerializer,
    MangaListSerializer,
    MangaDetailSerializer,
    MangaEpisodeSerializer,
    MappingCardSerializer,
    MappingSearchResultSerializer,
)
from .services import get_home_data, get_recommended_mappings, search_works


class HomeAPIView(APIView):
    def get(self, request):
        home_data = get_home_data()

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


class MangaEpisodesAPIView(APIView):
    def get(self, request, manga_id):
        if not Manga.objects.filter(id=manga_id).exists():
            return Response(
                {"detail": "Manga not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        episodes = MangaEpisode.objects.filter(manga_id=manga_id)

        volume = request.query_params.get("volume")
        if volume:
            episodes = episodes.filter(volume_number=volume)

        serializer = MangaEpisodeSerializer(episodes, many=True)

        return Response(
            {
                "manga_id": manga_id,
                "count": episodes.count(),
                "results": serializer.data,
            }
        )


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

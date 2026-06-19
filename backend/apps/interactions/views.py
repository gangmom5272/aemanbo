from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.works.models import Anime, Manga

from .models import AnimeComment, CommentStatus, Favorite, MangaComment
from .serializers import (
    AnimeCommentSerializer,
    FavoriteCreateSerializer,
    FavoriteSerializer,
    MangaCommentSerializer,
    MyCommentSerializer,
)
from .services import create_favorite, delete_favorite


class FavoriteAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            favorite, created = create_favorite(
                user=request.user,
                target_type=serializer.validated_data["target_type"],
                target_id=serializer.validated_data["target_id"],
                status_label=serializer.validated_data.get("status_label", ""),
            )
        except (Anime.DoesNotExist, Manga.DoesNotExist):
            return Response(
                {"detail": "Favorite target not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(FavoriteSerializer(favorite).data, status=response_status)


class FavoriteDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, favorite_id):
        favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
        delete_favorite(favorite)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyFavoritesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).order_by(
            "-created_at",
            "-id",
        )
        serializer = FavoriteSerializer(favorites, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})


class MyCommentsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        anime_comments = AnimeComment.objects.select_related("anime").filter(
            user=request.user,
        )
        manga_comments = MangaComment.objects.select_related("manga").filter(
            user=request.user,
        )
        comments = [
            {
                "id": comment.id,
                "target_type": "ANIME",
                "target_id": comment.anime_id,
                "target_title": comment.anime.title,
                "content": comment.content,
                "status": comment.status,
                "created_at": comment.created_at,
            }
            for comment in anime_comments
        ] + [
            {
                "id": comment.id,
                "target_type": "MANGA",
                "target_id": comment.manga_id,
                "target_title": comment.manga.title,
                "content": comment.content,
                "status": comment.status,
                "created_at": comment.created_at,
            }
            for comment in manga_comments
        ]
        comments.sort(key=lambda comment: comment["created_at"], reverse=True)

        serializer = MyCommentSerializer(comments, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})


class AnimeCommentsAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, anime_id):
        anime = get_object_or_404(Anime, id=anime_id)
        comments = AnimeComment.objects.select_related("user").filter(
            anime=anime,
            status=CommentStatus.ACTIVE,
        )
        serializer = AnimeCommentSerializer(comments, many=True)
        return Response(
            {
                "anime_id": anime.id,
                "count": len(serializer.data),
                "results": serializer.data,
            }
        )

    def post(self, request, anime_id):
        anime = get_object_or_404(Anime, id=anime_id)
        serializer = AnimeCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(anime=anime, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MangaCommentsAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, manga_id):
        manga = get_object_or_404(Manga, id=manga_id)
        comments = MangaComment.objects.select_related("user").filter(
            manga=manga,
            status=CommentStatus.ACTIVE,
        )
        serializer = MangaCommentSerializer(comments, many=True)
        return Response(
            {
                "manga_id": manga.id,
                "count": len(serializer.data),
                "results": serializer.data,
            }
        )

    def post(self, request, manga_id):
        manga = get_object_or_404(Manga, id=manga_id)
        serializer = MangaCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(manga=manga, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

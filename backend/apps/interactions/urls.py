from django.urls import path

from .views import (
    AnimeCommentsAPIView,
    FavoriteAPIView,
    FavoriteDetailAPIView,
    MangaCommentsAPIView,
    MyCommentsAPIView,
    MyFavoritesAPIView,
)

app_name = "interactions"

urlpatterns = [
    path("favorites/", FavoriteAPIView.as_view(), name="favorite-create"),
    path(
        "favorites/<int:favorite_id>/",
        FavoriteDetailAPIView.as_view(),
        name="favorite-detail",
    ),
    path("users/me/favorites/", MyFavoritesAPIView.as_view(), name="me-favorites"),
    path("users/me/comments/", MyCommentsAPIView.as_view(), name="me-comments"),
    path(
        "animes/<int:anime_id>/comments/",
        AnimeCommentsAPIView.as_view(),
        name="anime-comments",
    ),
    path(
        "mangas/<int:manga_id>/comments/",
        MangaCommentsAPIView.as_view(),
        name="manga-comments",
    ),
]

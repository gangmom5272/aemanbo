from django.urls import path

from .views import (
    AnimeDetailAPIView,
    AnimeListAPIView,
    MangaListAPIView,
    AnimeMangaMappingsAPIView,
    GenreListAPIView,
    HomeAPIView,
    MangaAnimeMappingsAPIView,
    MangaDetailAPIView,
    MappingRecommendationsAPIView,
    SearchAPIView,
)

app_name = "works"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("genres/", GenreListAPIView.as_view(), name="genre-list"),
    path("search/", SearchAPIView.as_view(), name="search"),
    path(
        "mappings/recommendations/",
        MappingRecommendationsAPIView.as_view(),
        name="mapping-recommendations",
    ),
    path("animes/", AnimeListAPIView.as_view(), name="anime-list"),
    path("mangas/", MangaListAPIView.as_view(), name="manga-list"),
    path("animes/<int:anime_id>/", AnimeDetailAPIView.as_view(), name="anime-detail"),
    path(
        "animes/<int:anime_id>/manga-mappings/",
        AnimeMangaMappingsAPIView.as_view(),
        name="anime-manga-mappings",
    ),
    path("mangas/<int:manga_id>/", MangaDetailAPIView.as_view(), name="manga-detail"),
    path(
        "mangas/<int:manga_id>/anime-mappings/",
        MangaAnimeMappingsAPIView.as_view(),
        name="manga-anime-mappings",
    ),
]

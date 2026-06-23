from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    Anime,
    AnimeMangaMapping,
    AnimeTag,
    Manga,
    MangaTag,
    MetadataTag,
)


class DetailMappingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.anime = Anime.objects.create(
            title="Jujutsu Kaisen",
            original_title="Jujutsu Kaisen Original",
            poster_image_url="https://example.com/jujutsu-poster.jpg",
            banner_image_url="https://example.com/jujutsu-banner.jpg",
            type=Anime.AnimeType.TVA,
            release_year=2020,
            episode_count=24,
            status=Anime.WorkStatus.COMPLETED,
            studio="MAPPA",
            synopsis="A dark fantasy anime about cursed energy.",
            rating_avg=4.7,
            rating_count=120,
            favorite_count=50,
        )
        self.manga = Manga.objects.create(
            title="Jujutsu Kaisen",
            original_title="Jujutsu Kaisen Manga Original",
            cover_image_url="https://example.com/jujutsu-cover.jpg",
            banner_image_url="https://example.com/jujutsu-manga-banner.jpg",
            author="Gege Akutami",
            publisher="Shueisha",
            description="A battle manga about sorcerers and curses.",
            status=Manga.MangaStatus.ONGOING,
            rating_avg=4.8,
            rating_count=180,
            favorite_count=70,
        )

        action = MetadataTag.objects.create(name="Action", type=MetadataTag.TagType.GENRE)
        dark_fantasy = MetadataTag.objects.create(
            name="Dark Fantasy",
            type=MetadataTag.TagType.GENRE,
        )
        studio = MetadataTag.objects.create(name="MAPPA", type=MetadataTag.TagType.STUDIO)

        AnimeTag.objects.create(anime=self.anime, tag=action)
        AnimeTag.objects.create(anime=self.anime, tag=dark_fantasy)
        AnimeTag.objects.create(anime=self.anime, tag=studio)

        MangaTag.objects.create(manga=self.manga, tag=action)
        MangaTag.objects.create(manga=self.manga, tag=dark_fantasy)

        self.mapping = AnimeMangaMapping.objects.create(
            anime=self.anime,
            manga=self.manga,
            anime_season_label="Season 1",
            anime_episode_from=1,
            anime_episode_to=24,
            manga_volume_from=1,
            manga_volume_to=8,
            manga_chapter_from=1,
            manga_chapter_to=63,
            continue_volume=8,
            continue_chapter=64,
            mapping_text="Continue from manga volume 8 chapter 64 after season 1.",
            description="Season 1 covers up to chapter 63.",
            source_note="Seed data for API tests.",
        )

    def test_anime_detail_api_returns_anime(self):
        url = reverse("works:anime-detail", args=[self.anime.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.anime.id)
        self.assertEqual(response.data["title"], "Jujutsu Kaisen")
        self.assertEqual(len(response.data["tags"]), 3)

    def test_anime_detail_api_returns_404_for_missing_anime(self):
        url = reverse("works:anime-detail", args=[99999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Anime not found.")

    def test_anime_manga_mappings_api_returns_mappings(self):
        url = reverse("works:anime-manga-mappings", args=[self.anime.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["anime_id"], self.anime.id)
        self.assertEqual(len(response.data["mappings"]), 1)
        self.assertEqual(response.data["mappings"][0]["manga"]["id"], self.manga.id)

    def test_manga_detail_api_returns_manga(self):
        url = reverse("works:manga-detail", args=[self.manga.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.manga.id)
        self.assertEqual(response.data["title"], "Jujutsu Kaisen")
        self.assertEqual(len(response.data["tags"]), 2)

    def test_manga_detail_api_returns_404_for_missing_manga(self):
        url = reverse("works:manga-detail", args=[99999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Manga not found.")

    def test_manga_anime_mappings_api_returns_mappings(self):
        url = reverse("works:manga-anime-mappings", args=[self.manga.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["manga_id"], self.manga.id)
        self.assertEqual(len(response.data["mappings"]), 1)
        self.assertEqual(response.data["mappings"][0]["anime"]["id"], self.anime.id)


class HomeSearchRecommendationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.anime = Anime.objects.create(
            title="Jujutsu Kaisen",
            original_title="Jujutsu Kaisen Original",
            poster_image_url="https://example.com/jujutsu-anime.jpg",
            status=Anime.WorkStatus.COMPLETED,
            release_year=2020,
            rating_avg=4.7,
            favorite_count=100,
        )
        self.manga = Manga.objects.create(
            title="Jujutsu Kaisen",
            original_title="Jujutsu Kaisen Manga Original",
            cover_image_url="https://example.com/jujutsu-manga.jpg",
            status=Manga.MangaStatus.ONGOING,
            rating_avg=4.8,
            favorite_count=120,
        )
        self.mapping = AnimeMangaMapping.objects.create(
            anime=self.anime,
            manga=self.manga,
            anime_season_label="Season 1",
            anime_episode_from=1,
            anime_episode_to=24,
            continue_volume=8,
            continue_chapter=64,
            mapping_text="Continue from manga volume 8 chapter 64 after season 1.",
        )

    def test_home_api_returns_initial_sections(self):
        response = self.client.get(reverse("works:home"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommended_mappings", response.data)
        self.assertIn("popular_animes", response.data)
        self.assertIn("popular_mangas", response.data)
        self.assertEqual(response.data["recommended_mappings"][0]["id"], self.mapping.id)
        self.assertEqual(response.data["popular_animes"][0]["id"], self.anime.id)
        self.assertEqual(response.data["popular_mangas"][0]["id"], self.manga.id)

    def test_search_api_returns_grouped_results(self):
        response = self.client.get(reverse("works:search"), {"keyword": "Jujutsu"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["keyword"], "Jujutsu")
        self.assertEqual(response.data["animes"][0]["id"], self.anime.id)
        self.assertEqual(response.data["mangas"][0]["id"], self.manga.id)
        self.assertEqual(response.data["mappings"][0]["id"], self.mapping.id)
        self.assertEqual(response.data["mappings"][0]["anime_title"], self.anime.title)
        self.assertEqual(response.data["mappings"][0]["manga_title"], self.manga.title)

    def test_search_api_returns_400_without_keyword(self):
        response = self.client.get(reverse("works:search"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "keyword query parameter is required.",
        )

    def test_recommendations_api_returns_mapping_cards(self):
        response = self.client.get(reverse("works:mapping-recommendations"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.mapping.id)
        self.assertEqual(
            response.data["results"][0]["mapping_text"],
            self.mapping.mapping_text,
        )
        self.assertEqual(response.data["results"][0]["anime"]["id"], self.anime.id)
        self.assertEqual(response.data["results"][0]["manga"]["id"], self.manga.id)

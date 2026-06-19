from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.works.models import Anime, Manga

from .models import AnimeComment, Favorite, MangaComment


class InteractionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="tester",
            nickname="tester",
            email="tester@example.com",
            password="password",
        )
        self.anime = Anime.objects.create(
            title="Jujutsu Kaisen",
            status=Anime.WorkStatus.COMPLETED,
            favorite_count=0,
        )
        self.manga = Manga.objects.create(
            title="Jujutsu Kaisen",
            status=Manga.MangaStatus.ONGOING,
            favorite_count=0,
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_favorite_api(self):
        self.authenticate()

        response = self.client.post(
            reverse("interactions:favorite-create"),
            {
                "target_type": "ANIME",
                "target_id": self.anime.id,
                "status_label": "Watching",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["target_type"], "ANIME")
        self.assertEqual(response.data["target"]["id"], self.anime.id)
        self.anime.refresh_from_db()
        self.assertEqual(self.anime.favorite_count, 1)

    def test_delete_favorite_api(self):
        self.authenticate()
        favorite = Favorite.objects.create(
            user=self.user,
            target_type=Favorite.TargetType.MANGA,
            target_id=self.manga.id,
        )
        self.manga.favorite_count = 1
        self.manga.save(update_fields=["favorite_count"])

        response = self.client.delete(
            reverse("interactions:favorite-detail", args=[favorite.id]),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(id=favorite.id).exists())
        self.manga.refresh_from_db()
        self.assertEqual(self.manga.favorite_count, 0)

    def test_my_favorites_api(self):
        self.authenticate()
        Favorite.objects.create(
            user=self.user,
            target_type=Favorite.TargetType.ANIME,
            target_id=self.anime.id,
        )

        response = self.client.get(reverse("interactions:me-favorites"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["target"]["id"], self.anime.id)

    def test_anime_comments_api_create_and_list(self):
        self.authenticate()

        create_response = self.client.post(
            reverse("interactions:anime-comments", args=[self.anime.id]),
            {"content": "Great adaptation."},
            format="json",
        )
        list_response = self.client.get(
            reverse("interactions:anime-comments", args=[self.anime.id]),
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["content"], "Great adaptation.")

    def test_manga_comments_api_create_and_list(self):
        self.authenticate()

        create_response = self.client.post(
            reverse("interactions:manga-comments", args=[self.manga.id]),
            {"content": "The next chapter is excellent."},
            format="json",
        )
        list_response = self.client.get(
            reverse("interactions:manga-comments", args=[self.manga.id]),
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(
            list_response.data["results"][0]["content"],
            "The next chapter is excellent.",
        )

    def test_my_comments_api(self):
        self.authenticate()
        AnimeComment.objects.create(
            anime=self.anime,
            user=self.user,
            content="Anime comment.",
        )
        MangaComment.objects.create(
            manga=self.manga,
            user=self.user,
            content="Manga comment.",
        )

        response = self.client.get(reverse("interactions:me-comments"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            {comment["target_type"] for comment in response.data["results"]},
            {"ANIME", "MANGA"},
        )

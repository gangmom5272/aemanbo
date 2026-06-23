from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Anime(TimeStampedModel):
    class AnimeType(models.TextChoices):
        TVA = "TVA", "TVA"
        MOVIE = "MOVIE", "Movie"
        OVA = "OVA", "OVA"

    class WorkStatus(models.TextChoices):
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"
        UPCOMING = "UPCOMING", "Upcoming"

    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    poster_image_url = models.URLField(max_length=500, blank=True)
    banner_image_url = models.URLField(max_length=500, blank=True)
    type = models.CharField(
        max_length=30,
        choices=AnimeType.choices,
        blank=True,
    )
    release_year = models.PositiveIntegerField(null=True, blank=True)
    episode_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=WorkStatus.choices,
        default=WorkStatus.ONGOING,
    )
    studio = models.CharField(max_length=100, blank=True)
    synopsis = models.TextField(blank=True)
    rating_avg = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(
        "MetadataTag",
        through="AnimeTag",
        related_name="animes",
        blank=True,
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Manga(TimeStampedModel):
    class MangaStatus(models.TextChoices):
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    cover_image_url = models.URLField(max_length=500, blank=True)
    banner_image_url = models.URLField(max_length=500, blank=True)
    author = models.CharField(max_length=100, blank=True)
    illustrator = models.CharField(max_length=100, blank=True)
    publisher = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=MangaStatus.choices,
        default=MangaStatus.ONGOING,
    )
    rating_avg = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(
        "MetadataTag",
        through="MangaTag",
        related_name="mangas",
        blank=True,
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class AnimeMangaMapping(TimeStampedModel):
    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name="manga_mappings",
    )
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name="anime_mappings",
    )
    anime_season_label = models.CharField(max_length=50, blank=True)
    anime_episode_from = models.PositiveIntegerField(null=True, blank=True)
    anime_episode_to = models.PositiveIntegerField(null=True, blank=True)
    manga_volume_from = models.PositiveIntegerField(null=True, blank=True)
    manga_volume_to = models.PositiveIntegerField(null=True, blank=True)
    manga_chapter_from = models.PositiveIntegerField(null=True, blank=True)
    manga_chapter_to = models.PositiveIntegerField(null=True, blank=True)
    continue_volume = models.PositiveIntegerField(null=True, blank=True)
    continue_chapter = models.PositiveIntegerField(null=True, blank=True)
    mapping_text = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    source_note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["anime_id", "anime_episode_from", "id"]

    def __str__(self):
        return f"{self.anime.title} -> {self.manga.title}"


class MetadataTag(TimeStampedModel):
    class TagType(models.TextChoices):
        GENRE = "GENRE", "Genre"
        TAG = "TAG", "Tag"
        STUDIO = "STUDIO", "Studio"

    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TagType.choices)

    class Meta:
        ordering = ["type", "name"]

    def __str__(self):
        return self.name


class AnimeTag(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    tag = models.ForeignKey(MetadataTag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["anime", "tag"],
                name="unique_anime_tag",
            )
        ]

    def __str__(self):
        return f"{self.anime.title} - {self.tag.name}"


class MangaTag(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)
    tag = models.ForeignKey(MetadataTag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["manga", "tag"],
                name="unique_manga_tag",
            )
        ]

    def __str__(self):
        return f"{self.manga.title} - {self.tag.name}"

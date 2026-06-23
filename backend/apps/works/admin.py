from django.contrib import admin

from .models import (
    Anime,
    AnimeMangaMapping,
    AnimeTag,
    Manga,
    MangaTag,
    MetadataTag,
)


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "type", "release_year", "status", "rating_avg")
    search_fields = ("title", "original_title", "studio")
    list_filter = ("type", "status")


@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "publisher", "status", "rating_avg")
    search_fields = ("title", "original_title", "author", "publisher")
    list_filter = ("status",)


@admin.register(AnimeMangaMapping)
class AnimeMangaMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "anime", "manga", "mapping_text")
    search_fields = ("anime__title", "manga__title", "mapping_text")


@admin.register(MetadataTag)
class MetadataTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type")
    list_filter = ("type",)
    search_fields = ("name",)


admin.site.register(AnimeTag)
admin.site.register(MangaTag)

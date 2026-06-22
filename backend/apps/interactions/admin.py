from django.contrib import admin

from .models import AnimeComment, Favorite, MangaComment


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "status_label")
    list_filter = ("target_type",)
    search_fields = ("user__username",)


@admin.register(AnimeComment)
class AnimeCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "anime", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("content", "anime__title", "user__username")


@admin.register(MangaComment)
class MangaCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "manga", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("content", "manga__title", "user__username")

from django.contrib import admin

from .models import AnimeComment, Favorite, MangaComment


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "status_label", "created_at")
    list_filter = ("target_type",)
    search_fields = ("user__username", "status_label")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AnimeComment)
class AnimeCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "anime", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("anime__title", "user__username", "content")
    autocomplete_fields = ("anime", "user", "parent")
    readonly_fields = ("created_at", "updated_at", "deleted_at")


@admin.register(MangaComment)
class MangaCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "manga", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("manga__title", "user__username", "content")
    autocomplete_fields = ("manga", "user", "parent")
    readonly_fields = ("created_at", "updated_at", "deleted_at")

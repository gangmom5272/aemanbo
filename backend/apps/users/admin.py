from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SocialAccount, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "nickname", "email", "role", "status")
    list_filter = ("role", "status", "is_staff", "is_superuser")
    search_fields = ("username", "nickname", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "애만보 프로필",
            {
                "fields": (
                    "nickname",
                    "profile_image_url",
                    "role",
                    "status",
                    "joined_at",
                    "deleted_at",
                )
            },
        ),
    )


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "provider", "provider_user_id", "email")
    list_filter = ("provider",)
    search_fields = ("user__username", "provider_user_id", "email")

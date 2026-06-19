from django.db import transaction

from apps.works.models import Anime, Manga

from .models import Favorite


def get_favorite_target(target_type, target_id):
    normalized_type = target_type.upper()

    if normalized_type == Favorite.TargetType.ANIME:
        return Anime.objects.get(id=target_id)
    if normalized_type == Favorite.TargetType.MANGA:
        return Manga.objects.get(id=target_id)

    raise ValueError("target_type must be ANIME or MANGA")


@transaction.atomic
def create_favorite(user, target_type, target_id, status_label=""):
    target = get_favorite_target(target_type, target_id)
    favorite, created = Favorite.objects.get_or_create(
        user=user,
        target_type=target_type.upper(),
        target_id=target_id,
        defaults={"status_label": status_label},
    )

    if not created and favorite.status_label != status_label:
        favorite.status_label = status_label
        favorite.save(update_fields=["status_label", "updated_at"])

    if created:
        target.favorite_count += 1
        target.save(update_fields=["favorite_count", "updated_at"])

    return favorite, created


@transaction.atomic
def delete_favorite(favorite):
    target = get_favorite_target(favorite.target_type, favorite.target_id)
    favorite.delete()

    if target.favorite_count > 0:
        target.favorite_count -= 1
        target.save(update_fields=["favorite_count", "updated_at"])

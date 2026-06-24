"""
CSV 데이터셋을 DB에 적재하는 임포터.

  python manage.py import_dataset
  python manage.py import_dataset --works data/works.csv --episodes data/episodes.csv

- works.csv : 한 행 = 애니 + 원작 만화 + 매핑 + 태그
- episodes.csv : (선택) 만화 단행본/화 목록
모든 적재는 update_or_create 기반이라 여러 번 실행해도 중복되지 않습니다.
"""
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.works.models import (
    Anime,
    AnimeMangaMapping,
    AnimeTag,
    Manga,
    MangaTag,
    MetadataTag,
)


def s(v):
    return (v or "").strip()


def i(v):
    v = s(v)
    try:
        return int(v)
    except ValueError:
        return None


def dec(v):
    v = s(v)
    try:
        return float(v)
    except ValueError:
        return 0


def anime_type(v):
    v = s(v).upper()
    return v if v in {"TVA", "MOVIE", "OVA"} else ""


def anime_status(v):
    v = s(v).upper()
    return v if v in {"ONGOING", "COMPLETED", "UPCOMING"} else "COMPLETED"


def manga_status(v):
    v = s(v).upper()
    return v if v in {"ONGOING", "COMPLETED"} else "ONGOING"


class Command(BaseCommand):
    help = "data/works.csv (+episodes.csv)를 읽어 작품/매핑/태그/단행본을 적재합니다."

    def add_arguments(self, parser):
        base = Path(settings.BASE_DIR) / "data"
        parser.add_argument("--works", default=str(base / "works.csv"))
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="적재 전 기존 작품/매핑/태그를 모두 삭제 (옛 import로 누적된 중복 제거)",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        works_path = Path(opts["works"])

        if not works_path.exists():
            self.stderr.write(self.style.ERROR(f"파일 없음: {works_path}"))
            return

        if opts["fresh"]:
            # 누적된 중복(옛 제목 등) 제거를 위해 작품 관련 테이블 초기화
            AnimeMangaMapping.objects.all().delete()
            AnimeTag.objects.all().delete()
            MangaTag.objects.all().delete()
            Anime.objects.all().delete()
            Manga.objects.all().delete()
            MetadataTag.objects.all().delete()
            self.stdout.write(self.style.WARNING("기존 작품/매핑/태그 데이터 삭제 완료 (--fresh)"))

        n_anime = n_manga = n_map = n_tag = 0

        # utf-8-sig: 엑셀이 붙이는 BOM 처리
        with works_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if not s(row.get("anime_title")) and not s(row.get("manga_title")):
                    continue

                anime = manga = None

                if s(row.get("anime_title")):
                    anime, created = Anime.objects.update_or_create(
                        title=s(row["anime_title"]),
                        defaults={
                            "original_title": s(row.get("anime_original_title")),
                            "type": anime_type(row.get("anime_type")),
                            "release_year": i(row.get("anime_release_year")),
                            "episode_count": i(row.get("anime_episode_count")),
                            "status": anime_status(row.get("anime_status")),
                            "studio": s(row.get("anime_studio")),
                            "synopsis": s(row.get("anime_synopsis")),
                            "poster_image_url": s(row.get("anime_poster_image_url")),
                            "banner_image_url": s(row.get("anime_banner_image_url")),
                            "rating_avg": dec(row.get("anime_rating_avg")),
                            "rating_count": i(row.get("anime_rating_count")) or 0,
                            "favorite_count": i(row.get("anime_favorite_count")) or 0,
                        },
                    )
                    n_anime += 1

                if s(row.get("manga_title")):
                    manga, created = Manga.objects.update_or_create(
                        title=s(row["manga_title"]),
                        defaults={
                            "original_title": s(row.get("manga_original_title")),
                            "author": s(row.get("manga_author")),
                            "illustrator": s(row.get("manga_illustrator")),
                            "publisher": s(row.get("manga_publisher")),
                            "status": manga_status(row.get("manga_status")),
                            "description": s(row.get("manga_description")),
                            "cover_image_url": s(row.get("manga_cover_image_url")),
                            "banner_image_url": s(row.get("manga_banner_image_url")),
                            "rating_avg": dec(row.get("manga_rating_avg")),
                            "rating_count": i(row.get("manga_rating_count")) or 0,
                            "favorite_count": i(row.get("manga_favorite_count")) or 0,
                        },
                    )
                    n_manga += 1

                # 태그(장르 ; 구분) + 제작사 태그
                for name in [g.strip() for g in s(row.get("genres")).split(";") if g.strip()]:
                    tag, _ = MetadataTag.objects.get_or_create(
                        name=name, defaults={"type": MetadataTag.TagType.GENRE}
                    )
                    if anime:
                        AnimeTag.objects.get_or_create(anime=anime, tag=tag)
                    if manga:
                        MangaTag.objects.get_or_create(manga=manga, tag=tag)
                    n_tag += 1

                if s(row.get("studio_tag")) and anime:
                    stag, _ = MetadataTag.objects.get_or_create(
                        name=s(row["studio_tag"]),
                        defaults={"type": MetadataTag.TagType.STUDIO},
                    )
                    AnimeTag.objects.get_or_create(anime=anime, tag=stag)

                # 매핑: 애니+만화 짝이 있으면 생성 (mapping_text 없으면 기본 문구).
                # 정확한 이어보기 지점(continue_*)은 이후 수동 검수로 채웁니다.
                if anime and manga:
                    mapping_text = s(row.get("mapping_text")) or "원작 만화 보기"
                    AnimeMangaMapping.objects.update_or_create(
                        anime=anime,
                        manga=manga,
                        anime_season_label=s(row.get("anime_season_label")),
                        defaults={
                            "anime_episode_from": i(row.get("anime_episode_from")),
                            "anime_episode_to": i(row.get("anime_episode_to")),
                            "manga_volume_from": i(row.get("manga_volume_from")),
                            "manga_volume_to": i(row.get("manga_volume_to")),
                            "manga_chapter_from": i(row.get("manga_chapter_from")),
                            "manga_chapter_to": i(row.get("manga_chapter_to")),
                            "continue_volume": i(row.get("continue_volume")),
                            "continue_chapter": i(row.get("continue_chapter")),
                            "mapping_text": mapping_text,
                            "description": s(row.get("mapping_description")),
                            "source_note": s(row.get("source_note")),
                        },
                    )
                    n_map += 1


        self.stdout.write(
            self.style.SUCCESS(
                f"적재 완료 — 애니 {n_anime}, 만화 {n_manga}, 매핑 {n_map}, 태그연결 {n_tag}"
            )
        )

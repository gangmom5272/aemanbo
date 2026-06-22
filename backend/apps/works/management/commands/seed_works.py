from django.core.management.base import BaseCommand

from apps.works.models import (
    Anime,
    AnimeMangaMapping,
    AnimeTag,
    Manga,
    MangaEpisode,
    MangaTag,
    MetadataTag,
)


WORK_SETS = [
    {
        "anime": {
            "title": "주술회전",
            "original_title": "呪術廻戦",
            "poster_image_url": "https://example.com/jujutsu-anime.jpg",
            "banner_image_url": "https://example.com/jujutsu-banner.jpg",
            "type": Anime.AnimeType.TVA,
            "release_year": 2020,
            "episode_count": 24,
            "status": Anime.WorkStatus.COMPLETED,
            "studio": "MAPPA",
            "synopsis": "저주를 둘러싼 싸움을 그린 다크 판타지 애니메이션.",
            "rating_avg": 4.7,
            "rating_count": 120,
            "favorite_count": 100,
        },
        "manga": {
            "title": "주술회전",
            "original_title": "呪術廻戦",
            "cover_image_url": "https://example.com/jujutsu-manga.jpg",
            "banner_image_url": "https://example.com/jujutsu-manga-banner.jpg",
            "author": "아쿠타미 게게",
            "publisher": "슈에이샤",
            "description": "저주와 주술사를 중심으로 전개되는 배틀 만화.",
            "status": Manga.MangaStatus.ONGOING,
            "rating_avg": 4.8,
            "rating_count": 180,
            "favorite_count": 120,
        },
        "tags": ["액션", "다크 판타지"],
        "studio_tag": "MAPPA",
        "episodes": [
            {"volume_number": 8, "chapter_number": 64, "title": "시부야 사변"},
            {"volume_number": 8, "chapter_number": 65, "title": "시부야 사변 2"},
        ],
        "mapping": {
            "anime_season_label": "Season 1",
            "anime_episode_from": 1,
            "anime_episode_to": 24,
            "manga_volume_from": 1,
            "manga_volume_to": 8,
            "manga_chapter_from": 1,
            "manga_chapter_to": 63,
            "continue_volume": 8,
            "continue_chapter": 64,
            "mapping_text": "애니 1기 이후 원작 만화 8권 64화부터",
            "description": "애니 1기는 원작 63화까지를 다룹니다.",
        },
    },
    {
        "anime": {
            "title": "귀멸의 칼날",
            "original_title": "鬼滅の刃",
            "poster_image_url": "https://example.com/demon-slayer-anime.jpg",
            "banner_image_url": "https://example.com/demon-slayer-banner.jpg",
            "type": Anime.AnimeType.TVA,
            "release_year": 2019,
            "episode_count": 26,
            "status": Anime.WorkStatus.COMPLETED,
            "studio": "Ufotable",
            "synopsis": "가족을 잃은 소년이 혈귀와 맞서 싸우는 판타지 액션.",
            "rating_avg": 4.8,
            "rating_count": 200,
            "favorite_count": 150,
        },
        "manga": {
            "title": "귀멸의 칼날",
            "original_title": "鬼滅の刃",
            "cover_image_url": "https://example.com/demon-slayer-manga.jpg",
            "banner_image_url": "https://example.com/demon-slayer-manga-banner.jpg",
            "author": "고토게 코요하루",
            "publisher": "슈에이샤",
            "description": "혈귀가 된 여동생을 되돌리기 위한 여정을 그린 만화.",
            "status": Manga.MangaStatus.COMPLETED,
            "rating_avg": 4.7,
            "rating_count": 220,
            "favorite_count": 160,
        },
        "tags": ["액션", "판타지"],
        "studio_tag": "Ufotable",
        "episodes": [
            {"volume_number": 8, "chapter_number": 67, "title": "상현 집결"},
            {"volume_number": 8, "chapter_number": 68, "title": "사용되는 자"},
        ],
        "mapping": {
            "anime_season_label": "무한열차편",
            "anime_episode_from": 1,
            "anime_episode_to": 7,
            "manga_volume_from": 7,
            "manga_volume_to": 8,
            "manga_chapter_from": 54,
            "manga_chapter_to": 66,
            "continue_volume": 8,
            "continue_chapter": 67,
            "mapping_text": "무한열차편 이후 원작 만화 8권 67화부터",
            "description": "무한열차편 이후 이야기는 원작 67화부터 이어집니다.",
        },
    },
    {
        "anime": {
            "title": "체인소 맨",
            "original_title": "チェンソーマン",
            "poster_image_url": "https://example.com/chainsaw-man-anime.jpg",
            "banner_image_url": "https://example.com/chainsaw-man-banner.jpg",
            "type": Anime.AnimeType.TVA,
            "release_year": 2022,
            "episode_count": 12,
            "status": Anime.WorkStatus.COMPLETED,
            "studio": "MAPPA",
            "synopsis": "악마와 계약한 소년 덴지의 피비린내 나는 성장담.",
            "rating_avg": 4.5,
            "rating_count": 130,
            "favorite_count": 95,
        },
        "manga": {
            "title": "체인소 맨",
            "original_title": "チェンソーマン",
            "cover_image_url": "https://example.com/chainsaw-man-manga.jpg",
            "banner_image_url": "https://example.com/chainsaw-man-manga-banner.jpg",
            "author": "후지모토 타츠키",
            "publisher": "슈에이샤",
            "description": "악마 사냥꾼 덴지를 중심으로 펼쳐지는 다크 액션 만화.",
            "status": Manga.MangaStatus.ONGOING,
            "rating_avg": 4.6,
            "rating_count": 160,
            "favorite_count": 110,
        },
        "tags": ["액션", "다크 판타지"],
        "studio_tag": "MAPPA",
        "episodes": [
            {"volume_number": 5, "chapter_number": 39, "title": "찢어지는 마음"},
            {"volume_number": 5, "chapter_number": 40, "title": "사랑, 꽃, 전기톱"},
        ],
        "mapping": {
            "anime_season_label": "Season 1",
            "anime_episode_from": 1,
            "anime_episode_to": 12,
            "manga_volume_from": 1,
            "manga_volume_to": 5,
            "manga_chapter_from": 1,
            "manga_chapter_to": 38,
            "continue_volume": 5,
            "continue_chapter": 39,
            "mapping_text": "애니 1기 이후 원작 만화 5권 39화부터",
            "description": "애니 1기는 원작 38화까지를 다룹니다.",
        },
    },
    {
        "anime": {
            "title": "스파이 패밀리",
            "original_title": "SPY×FAMILY",
            "poster_image_url": "https://example.com/spy-family-anime.jpg",
            "banner_image_url": "https://example.com/spy-family-banner.jpg",
            "type": Anime.AnimeType.TVA,
            "release_year": 2022,
            "episode_count": 25,
            "status": Anime.WorkStatus.COMPLETED,
            "studio": "WIT Studio / CloverWorks",
            "synopsis": "스파이, 암살자, 초능력자가 가족으로 위장하는 코미디 액션.",
            "rating_avg": 4.6,
            "rating_count": 170,
            "favorite_count": 140,
        },
        "manga": {
            "title": "스파이 패밀리",
            "original_title": "SPY×FAMILY",
            "cover_image_url": "https://example.com/spy-family-manga.jpg",
            "banner_image_url": "https://example.com/spy-family-manga-banner.jpg",
            "author": "엔도 타츠야",
            "publisher": "슈에이샤",
            "description": "가짜 가족이 각자의 비밀을 숨기며 임무를 수행하는 만화.",
            "status": Manga.MangaStatus.ONGOING,
            "rating_avg": 4.6,
            "rating_count": 150,
            "favorite_count": 130,
        },
        "tags": ["코미디", "액션"],
        "studio_tag": "WIT Studio",
        "episodes": [
            {"volume_number": 7, "chapter_number": 38, "title": "가족 임무"},
            {"volume_number": 7, "chapter_number": 39, "title": "다음 임무"},
        ],
        "mapping": {
            "anime_season_label": "Season 1",
            "anime_episode_from": 1,
            "anime_episode_to": 25,
            "manga_volume_from": 1,
            "manga_volume_to": 7,
            "manga_chapter_from": 1,
            "manga_chapter_to": 37,
            "continue_volume": 7,
            "continue_chapter": 38,
            "mapping_text": "애니 1기 이후 원작 만화 7권 38화부터",
            "description": "애니 1기 이후 원작은 38화부터 이어집니다.",
        },
    },
    {
        "anime": {
            "title": "진격의 거인",
            "original_title": "進撃の巨人",
            "poster_image_url": "https://example.com/attack-on-titan-anime.jpg",
            "banner_image_url": "https://example.com/attack-on-titan-banner.jpg",
            "type": Anime.AnimeType.TVA,
            "release_year": 2013,
            "episode_count": 25,
            "status": Anime.WorkStatus.COMPLETED,
            "studio": "WIT Studio",
            "synopsis": "거인에게 빼앗긴 세계에서 인류의 생존을 그린 다크 판타지.",
            "rating_avg": 4.9,
            "rating_count": 300,
            "favorite_count": 220,
        },
        "manga": {
            "title": "진격의 거인",
            "original_title": "進撃の巨人",
            "cover_image_url": "https://example.com/attack-on-titan-manga.jpg",
            "banner_image_url": "https://example.com/attack-on-titan-manga-banner.jpg",
            "author": "이사야마 하지메",
            "publisher": "코단샤",
            "description": "벽 안의 인류와 거인의 진실을 추적하는 만화.",
            "status": Manga.MangaStatus.COMPLETED,
            "rating_avg": 4.8,
            "rating_count": 280,
            "favorite_count": 210,
        },
        "tags": ["액션", "다크 판타지"],
        "studio_tag": "WIT Studio",
        "episodes": [
            {"volume_number": 9, "chapter_number": 34, "title": "전사의 춤"},
            {"volume_number": 9, "chapter_number": 35, "title": "짐승 거인"},
        ],
        "mapping": {
            "anime_season_label": "Season 1",
            "anime_episode_from": 1,
            "anime_episode_to": 25,
            "manga_volume_from": 1,
            "manga_volume_to": 8,
            "manga_chapter_from": 1,
            "manga_chapter_to": 33,
            "continue_volume": 9,
            "continue_chapter": 34,
            "mapping_text": "애니 1기 이후 원작 만화 9권 34화부터",
            "description": "애니 1기는 원작 33화까지를 다룹니다.",
        },
    },
]


class Command(BaseCommand):
    help = "Seed initial anime, manga, mapping, tag, and episode data."

    def handle(self, *args, **options):
        created_count = 0

        for work_set in WORK_SETS:
            anime, anime_created = Anime.objects.update_or_create(
                title=work_set["anime"]["title"],
                defaults=work_set["anime"],
            )
            manga, _ = Manga.objects.update_or_create(
                title=work_set["manga"]["title"],
                defaults=work_set["manga"],
            )

            if anime_created:
                created_count += 1

            tag_names = work_set["tags"]
            for tag_name in tag_names:
                tag, _ = MetadataTag.objects.get_or_create(
                    name=tag_name,
                    defaults={"type": MetadataTag.TagType.GENRE},
                )
                AnimeTag.objects.get_or_create(anime=anime, tag=tag)
                MangaTag.objects.get_or_create(manga=manga, tag=tag)

            studio_tag, _ = MetadataTag.objects.get_or_create(
                name=work_set["studio_tag"],
                defaults={"type": MetadataTag.TagType.STUDIO},
            )
            AnimeTag.objects.get_or_create(anime=anime, tag=studio_tag)

            for episode_data in work_set["episodes"]:
                MangaEpisode.objects.update_or_create(
                    manga=manga,
                    volume_number=episode_data["volume_number"],
                    chapter_number=episode_data["chapter_number"],
                    defaults={
                        "title": episode_data["title"],
                        "rating_avg": episode_data.get("rating_avg", 0),
                    },
                )

            AnimeMangaMapping.objects.update_or_create(
                anime=anime,
                manga=manga,
                anime_season_label=work_set["mapping"]["anime_season_label"],
                defaults=work_set["mapping"],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(WORK_SETS)} work sets. Created {created_count} anime records."
            )
        )

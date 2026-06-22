from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.works.models import Anime, Manga
from apps.interactions.models import AnimeComment, MangaComment
from apps.interactions.services import create_favorite

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "데모용 목 데이터: 작품 시드 + 데모 유저 + 찜 + 댓글을 생성합니다."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) 작품/매핑/단행본 시드 (이미 있으면 갱신)
        call_command("seed_works")

        # 2) 데모 유저(관리자) 생성 — /admin 로그인으로 인증 기능 테스트
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(username=DEMO_USERNAME).first()
        if user is None:
            user = User.objects.create_superuser(
                username=DEMO_USERNAME,
                email="demo@aemanbo.local",
                password=DEMO_PASSWORD,
                nickname="데모유저",
            )
            self.stdout.write(
                self.style.SUCCESS(f"데모 유저 생성: {DEMO_USERNAME} / {DEMO_PASSWORD}")
            )
        else:
            self.stdout.write(f"데모 유저 이미 존재: {DEMO_USERNAME}")

        # 3) 찜 데이터 (애니 2 + 만화 2)
        fav_count = 0
        for title in ["주술회전", "체인소 맨"]:
            anime = Anime.objects.filter(title=title).first()
            if anime:
                _, created = create_favorite(user, "ANIME", anime.id, status_label="시청중")
                fav_count += 1 if created else 0
        for title in ["진격의 거인", "스파이 패밀리"]:
            manga = Manga.objects.filter(title=title).first()
            if manga:
                _, created = create_favorite(user, "MANGA", manga.id, status_label="읽는중")
                fav_count += 1 if created else 0

        # 4) 댓글 데이터
        cmt_count = 0
        anime = Anime.objects.filter(title="주술회전").first()
        if anime:
            _, created = AnimeComment.objects.get_or_create(
                anime=anime,
                user=user,
                content="1기 보고 바로 원작으로 넘어갔어요. 매핑 정확하네요 👍",
            )
            cmt_count += 1 if created else 0
        manga = Manga.objects.filter(title="진격의 거인").first()
        if manga:
            _, created = MangaComment.objects.get_or_create(
                manga=manga,
                user=user,
                content="애니로 어디까지 봤는지 헷갈렸는데 여기서 정리됨.",
            )
            cmt_count += 1 if created else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"완료 — 찜 {fav_count}건, 댓글 {cmt_count}건 추가 (유저: {DEMO_USERNAME})"
            )
        )

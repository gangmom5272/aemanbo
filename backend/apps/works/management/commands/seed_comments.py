# -*- coding: utf-8 -*-
"""
발표 시연용 더미 댓글 시드.

  python manage.py seed_comments               # 귀멸 집중 + 인기작 일반 채우기
  python manage.py seed_comments --kimetsu 12  # 귀멸 작품당 댓글 수
  python manage.py seed_comments --works 30    # 일반 채울 상위 N개 애니/만화

- 더미 유저 여러 명을 만들고, 시연 동선(귀멸의 칼날)의 만화 + 모든 애니 시즌에 댓글을 많이 채웁니다.
- 그 외 인기작에도 적당히 댓글을 깔아 '텅 빈 화면'을 방지합니다.
- 재실행해도 누적되지 않도록, 더미 유저가 쓴 기존 댓글을 먼저 지우고 다시 채웁니다.
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.interactions.models import AnimeComment, MangaComment
from apps.works.models import Anime, Manga

User = get_user_model()

DUMMY_USERS = [
    ("anifan01", "정주행머신"),
    ("anifan02", "만화는원작파"),
    ("anifan03", "작화찬양러"),
    ("anifan04", "OST수집가"),
    ("anifan05", "주말덕질러"),
    ("anifan06", "스포는싫어"),
    ("anifan07", "입덕요정"),
    ("anifan08", "회차정주행"),
    ("anifan09", "심야애니러"),
    ("anifan10", "원작은성경"),
    ("anifan11", "탄지로팬클럽"),
    ("anifan12", "네즈코지킴이"),
    ("anifan13", "히노카미러"),
    ("anifan14", "물의호흡5형"),
    ("anifan15", "코믹덕후777"),
    ("anifan16", "애니메순례자"),
    ("anifan17", "콜라보러버"),
    ("anifan18", "정주행각잡음"),
]

# 귀멸의 칼날 전용(작품 맥락이 있는) 댓글
KIMETSU = [
    "탄지로 진짜 착해서 더 응원하게 됨",
    "네즈코 너무 귀여워서 지켜주고 싶다",
    "ufotable 작화 미쳤다 거의 극장판 수준",
    "OST 들으면 소름… 카마도 탄지로의 노래 ㄷㄷ",
    "전투씬 작화에 입 벌리고 봤음",
    "1기 보고 바로 원작 정주행 들어갔어요",
    "히노카미 카구라 장면 몇 번을 돌려봤는지",
    "감정선 잡는 연출이 진짜 잘 만들었다",
    "물의 호흡 작화 보려고 또 정주행함",
    "탄지로 성장 서사 보며 같이 큰 기분",
    "악귀들도 서사가 있어서 마냥 미워할 수가 없음",
    "주제가까지 완벽한 작품 인정합니다",
    "처음 봤을 때 충격을 아직도 못 잊음",
    "원작도 명작이라 같이 보는 거 강추",
    "이거 보고 애니 입문했어요",
    "렌고쿠 형님… 마음에 새겼습니다",
    "음주(音柱) 등장씬 간지 폭발",
    "도공 마을편 작화도 여전히 미쳤더라",
    "다음 시즌 언제 나오나요 진짜 못 기다림",
    "작붕 하나 없는 퀄리티에 박수",
    "네즈코 박스 밈 아직도 웃김ㅋㅋ",
    "정주행 시작하면 밤새는 거 주의",
    "친구한테 영업했더니 같이 덕질 중",
    "이어보기 정보 덕분에 원작 바로 시작함 감사",
    "탄지로 가족 생각하면 또 눈물난다",
    "OST 전곡 플레이리스트에 넣었음",
    "이 작품 안 본 사람 부럽다 처음 보고 싶다",
    "명작은 명작이다 띵작 ㅇㅈ",
]

# 그 외 작품 범용 댓글
GENERAL = [
    "작화 미쳤다… 명장면 계속 돌려봄",
    "1기 정주행 끝! 바로 원작 보러 갑니다",
    "이거 보고 완전 입덕했어요",
    "스토리 몰입감 진짜 장난 아님",
    "OST가 반은 했다 진짜 명곡",
    "다음 시즌 언제 나오나요ㅠㅠ",
    "원작이랑 비교해서 보는 재미가 쏠쏠",
    "캐릭터 서사 너무 좋아서 눈물남",
    "연출 보는 맛에 정주행함",
    "이 작품 안 본 사람 부럽다",
    "여기서부터 원작으로 넘어가니 더 깊더라",
    "분위기 미쳤고 후반부 전개 소름",
    "친구한테 강추했더니 같이 덕질 중",
    "작붕 하나 없이 퀄 유지하는 거 대단",
    "이어보기 정보 덕분에 원작 바로 시작함",
    "명작은 명작이다 띵작 인정",
    "한 번 보기 시작하면 못 멈춤 주의",
    "주인공 성장 서사 진짜 잘 뽑음",
]


class Command(BaseCommand):
    help = "시연용 더미 댓글을 귀멸 작품에 집중 + 인기작에 채웁니다."

    def add_arguments(self, parser):
        parser.add_argument("--kimetsu", type=int, default=12, help="귀멸 작품당 댓글 수(평균)")
        parser.add_argument("--per", type=int, default=4, help="일반 작품당 댓글 수(평균)")
        parser.add_argument("--works", type=int, default=30, help="일반으로 채울 상위 N개")

    def handle(self, *args, **opts):
        rnd = random.Random(42)
        now = timezone.now()

        # 1) 더미 유저 확보 (+ 무료 아바타 프로필 사진)
        AVATAR_STYLES = ["adventurer", "avataaars", "fun-emoji", "micah", "thumbs", "bottts"]
        users = []
        for i, (uname, nick) in enumerate(DUMMY_USERS):
            u, created = User.objects.get_or_create(
                username=uname, defaults={"nickname": nick, "role": "USER"}
            )
            if created:
                u.set_unusable_password()
            # DiceBear 무료 아바타 (username 기반 결정적 생성)
            style = AVATAR_STYLES[i % len(AVATAR_STYLES)]
            u.profile_image_url = f"https://api.dicebear.com/9.x/{style}/png?seed={uname}"
            u.save()
            users.append(u)

        # 2) 재실행 대비 초기화
        AnimeComment.objects.filter(user__in=users).delete()
        MangaComment.objects.filter(user__in=users).delete()

        def add_comments(work, CommentModel, fk, pool, count):
            count = min(count, len(pool))
            texts = rnd.sample(pool, count)
            us = users[:]
            rnd.shuffle(us)
            n = 0
            for idx, text in enumerate(texts):
                u = us[idx % len(us)]  # 가능한 한 서로 다른 유저
                c = CommentModel.objects.create(**{fk: work, "user": u, "content": text})
                ts = now - timedelta(
                    days=rnd.randint(0, 45), hours=rnd.randint(0, 23), minutes=rnd.randint(0, 59)
                )
                CommentModel.objects.filter(id=c.id).update(created_at=ts)
                n += 1
            return n

        # 3) 귀멸 집중 (만화 + 모든 애니 시즌)
        kim = opts["kimetsu"]
        na = nm = 0
        kim_animes = list(Anime.objects.filter(title__icontains="귀멸"))
        kim_mangas = list(Manga.objects.filter(title__icontains="귀멸"))
        for a in kim_animes:
            na += add_comments(a, AnimeComment, "anime", KIMETSU, rnd.randint(kim - 2, kim + 2))
        for m in kim_mangas:
            nm += add_comments(m, MangaComment, "manga", KIMETSU, rnd.randint(kim, kim + 3))

        # 4) 일반 인기작 (귀멸 제외)
        per = opts["per"]; topn = opts["works"]
        gen_animes = list(
            Anime.objects.exclude(title__icontains="귀멸")
            .order_by("-favorite_count", "-rating_avg", "title")[:topn]
        )
        gen_mangas = list(
            Manga.objects.exclude(title__icontains="귀멸")
            .order_by("-favorite_count", "-rating_avg", "title")[:topn]
        )
        for a in gen_animes:
            na += add_comments(a, AnimeComment, "anime", GENERAL, rnd.randint(max(1, per - 2), per + 2))
        for m in gen_mangas:
            nm += add_comments(m, MangaComment, "manga", GENERAL, rnd.randint(max(1, per - 2), per + 2))

        self.stdout.write(self.style.SUCCESS(
            f"더미 댓글 생성 완료 — 유저 {len(users)}명 | 애니 댓글 {na} | 만화 댓글 {nm}\n"
            f"  · 귀멸 집중: 애니 {len(kim_animes)}작품, 만화 {len(kim_mangas)}작품\n"
            f"  · 일반: 애니 {len(gen_animes)}작품, 만화 {len(gen_mangas)}작품"
        ))

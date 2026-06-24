import difflib

from django.db.models import Q

from .models import Anime, AnimeMangaMapping, Manga


DEFAULT_SEARCH_LIMIT = 10
DEFAULT_RECOMMENDATION_LIMIT = 20
MAX_RECOMMENDATION_LIMIT = 50


def get_home_data(user=None):
    return {
        "recommended_mappings": get_recommended_mappings(limit=6, user=user),
        "popular_animes": Anime.objects.order_by(
            "-favorite_count",
            "-rating_avg",
            "title",
        )[:6],
        "popular_mangas": Manga.objects.order_by(
            "-favorite_count",
            "-rating_avg",
            "title",
        )[:6],
    }


def _partial_ratio(short, text):
    """short(검색어)를 text 안에서 슬라이딩하며 가장 비슷한 구간의 유사도(0~1)."""
    if not short or not text:
        return 0.0
    if short in text:
        return 1.0
    if len(short) > len(text):
        short, text = text, short
    n = len(short)
    best = 0.0
    for i in range(len(text) - n + 1):
        r = difflib.SequenceMatcher(None, short, text[i : i + n]).ratio()
        if r > best:
            best = r
    return best


def _fuzzy_fill(model, keyword, exclude_ids, need, fields, threshold=0.7):
    """substring으로 못 채운 만큼 오타 허용 매칭으로 보강."""
    if need <= 0:
        return []
    kw = keyword.lower()
    ranked = []
    for row in model.objects.exclude(id__in=exclude_ids).values("id", *fields):
        score = 0.0
        for f in fields:
            score = max(score, _partial_ratio(kw, (row.get(f) or "").lower()))
            if score >= 0.999:
                break
        if score >= threshold:
            ranked.append((score, row["id"]))
    ranked.sort(key=lambda x: x[0], reverse=True)
    ids = [rid for _, rid in ranked[:need]]
    if not ids:
        return []
    by_id = {obj.id: obj for obj in model.objects.filter(id__in=ids)}
    return [by_id[i] for i in ids if i in by_id]


def search_works(keyword, limit=DEFAULT_SEARCH_LIMIT):
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        raise ValueError("keyword is required")

    # 제목(+원제)만 검색 — 줄거리/제작사/작가 등은 검색 대상에서 제외
    anime_query = (
        Q(title__icontains=normalized_keyword)
        | Q(original_title__icontains=normalized_keyword)
    )
    manga_query = (
        Q(title__icontains=normalized_keyword)
        | Q(original_title__icontains=normalized_keyword)
    )
    mapping_query = (
        Q(mapping_text__icontains=normalized_keyword)
        | Q(anime__title__icontains=normalized_keyword)
        | Q(manga__title__icontains=normalized_keyword)
    )

    animes = list(
        Anime.objects.filter(anime_query).order_by("-favorite_count", "-rating_avg", "title")[:limit]
    )
    mangas = list(
        Manga.objects.filter(manga_query).order_by("-favorite_count", "-rating_avg", "title")[:limit]
    )

    # 오타/유사어 보강 (substring으로 못 채운 만큼)
    animes += _fuzzy_fill(
        Anime, normalized_keyword, [a.id for a in animes], limit - len(animes),
        ["title", "original_title"],
    )
    mangas += _fuzzy_fill(
        Manga, normalized_keyword, [m.id for m in mangas], limit - len(mangas),
        ["title", "original_title"],
    )

    return {
        "keyword": normalized_keyword,
        "animes": animes,
        "mangas": mangas,
        "mappings": AnimeMangaMapping.objects.select_related("anime", "manga")
        .filter(mapping_query)
        .order_by("-created_at", "-id")[:limit],
    }


def search_by_content(keyword, limit=12):
    """제목 검색이 0건일 때 폴백용: 줄거리/장르 등 본문에서 키워드 검색."""
    kw = (keyword or "").strip()
    if not kw:
        return {"animes": [], "mangas": []}
    anime_q = Q(synopsis__icontains=kw) | Q(tags__name__icontains=kw)
    manga_q = Q(description__icontains=kw) | Q(tags__name__icontains=kw)
    animes = list(
        Anime.objects.filter(anime_q).distinct()
        .order_by("-favorite_count", "-rating_avg", "title")[:limit]
    )
    mangas = list(
        Manga.objects.filter(manga_q).distinct()
        .order_by("-favorite_count", "-rating_avg", "title")[:limit]
    )
    return {"animes": animes, "mangas": mangas}


def get_recommended_mappings(limit=DEFAULT_RECOMMENDATION_LIMIT, user=None):
    safe_limit = max(1, min(limit, MAX_RECOMMENDATION_LIMIT))
    base = AnimeMangaMapping.objects.select_related("anime", "manga")

    prefs = []
    if user is not None and getattr(user, "is_authenticated", False):
        prefs = [g for g in (getattr(user, "preferred_genres", None) or []) if g]

    # 선호 장르가 없으면 기존처럼 전체 무작위
    if not prefs:
        return list(base.order_by("?")[:safe_limit])

    # 선호 장르 우선: 해당 장르 애니 매핑을 무작위로 채우고,
    # 부족하면 일반 무작위로 보강
    preferred = list(
        base.filter(anime__tags__name__in=prefs).distinct().order_by("?")[:safe_limit]
    )
    if len(preferred) < safe_limit:
        need = safe_limit - len(preferred)
        used_ids = [m.id for m in preferred]
        fill = list(
            base.exclude(id__in=used_ids).order_by("?")[:need]
        )
        preferred += fill
    return preferred[:safe_limit]

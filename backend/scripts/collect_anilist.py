"""
[1단계] AniList API만으로 '애니 기준' 데이터 수집 + 원작 만화 연결.

  cd backend
  python scripts/collect_anilist.py                 # 인기 애니 1000개 + 원작 만화
  python scripts/collect_anilist.py --count 300 --per-page 10

- 인기 애니(원작=만화)를 모으고, 각 애니의 relations에서 원작 만화(SOURCE)를 ID로 연결.
- 애니는 시즌(기)별로 별도 항목 → "여러 애니 → 하나 만화" 가 행으로 자연스럽게 표현됨.
- 이름 매칭이 전혀 없으므로 연결 정확도가 높습니다.
- 만화의 작가/그림작가는 여기선 비움(2단계나 추후 보강). 회차 매핑도 2단계에서.
- 429 자동 재시도 + 이어하기(out 존재 시 이미 받은 애니 건너뜀).

데이터 출처: AniList (https://anilist.co)
"""
import argparse
import csv
import os
import re
import sys
import time

import requests

ENDPOINT = "https://graphql.anilist.co"
QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage currentPage }
    media(type: ANIME, source: MANGA, sort: POPULARITY_DESC, isAdult: false) {
      title { romaji english native }
      format seasonYear episodes status averageScore
      coverImage { extraLarge large }
      bannerImage
      studios(isMain: true) { nodes { name } }
      description(asHtml: false)
      genres
      relations {
        edges {
          relationType
          node {
            type
            title { romaji english native }
            description(asHtml: false)
            coverImage { extraLarge large }
            bannerImage
            status genres averageScore
          }
        }
      }
    }
  }
}
"""

COLUMNS = [
    "anime_title", "anime_original_title", "anime_type", "anime_release_year",
    "anime_episode_count", "anime_status", "anime_studio", "anime_synopsis",
    "anime_poster_image_url", "anime_banner_image_url", "anime_rating_avg",
    "anime_rating_count", "anime_favorite_count",
    "manga_title", "manga_original_title", "manga_author", "manga_illustrator",
    "manga_publisher", "manga_status", "manga_description", "manga_cover_image_url",
    "manga_banner_image_url", "manga_rating_avg", "manga_rating_count",
    "manga_favorite_count", "genres", "studio_tag",
    "anime_season_label", "anime_episode_from", "anime_episode_to",
    "manga_volume_from", "manga_volume_to", "manga_chapter_from", "manga_chapter_to",
    "continue_volume", "continue_chapter", "mapping_text", "mapping_description",
    "source_note",
]
FORMAT_MAP = {"TV": "TVA", "TV_SHORT": "TVA", "ONA": "TVA", "MOVIE": "MOVIE", "OVA": "OVA", "SPECIAL": "OVA"}
A_STATUS = {"FINISHED": "COMPLETED", "RELEASING": "ONGOING", "NOT_YET_RELEASED": "UPCOMING", "CANCELLED": "COMPLETED", "HIATUS": "ONGOING"}
M_STATUS = {"FINISHED": "COMPLETED", "RELEASING": "ONGOING", "HIATUS": "ONGOING", "CANCELLED": "COMPLETED", "NOT_YET_RELEASED": "ONGOING"}


def strip_html(t):
    t = re.sub(r"<br\s*/?>", "\n", t or "", flags=re.I)
    return re.sub(r"<[^>]+>", "", t).strip()


def anilist_request(payload, max_retries=6):
    for attempt in range(max_retries):
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=25)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 60)) + 1
            print(f"    · 429 제한 — {wait}s 대기 후 재시도", flush=True)
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        try:
            r.raise_for_status()
        except requests.RequestException:
            return None
        return r.json()
    return None


def source_manga(media):
    for e in (media.get("relations") or {}).get("edges") or []:
        node = e.get("node") or {}
        if e.get("relationType") == "SOURCE" and node.get("type") == "MANGA":
            return node
    # 백업: SOURCE가 없으면 MANGA 타입 관계 중 첫 번째
    for e in (media.get("relations") or {}).get("edges") or []:
        node = e.get("node") or {}
        if node.get("type") == "MANGA":
            return node
    return None


def build_row(media):
    manga = source_manga(media)
    if not manga:
        return None
    at = media.get("title") or {}
    studios = ((media.get("studios") or {}).get("nodes")) or []
    studio = studios[0]["name"] if studios else ""
    a_score = media.get("averageScore")
    a_cov = media.get("coverImage") or {}
    mt = manga.get("title") or {}
    m_cov = manga.get("coverImage") or {}
    m_score = manga.get("averageScore")
    a_genres = media.get("genres") or []
    m_genres = manga.get("genres") or []
    genres = []
    for g in a_genres + m_genres:
        if g and g not in genres:
            genres.append(g)

    row = {c: "" for c in COLUMNS}
    row.update({
        "anime_title": at.get("english") or at.get("romaji") or "",
        "anime_original_title": at.get("native") or at.get("romaji") or "",
        "anime_type": FORMAT_MAP.get(media.get("format"), ""),
        "anime_release_year": media.get("seasonYear") or "",
        "anime_episode_count": media.get("episodes") or "",
        "anime_status": A_STATUS.get(media.get("status"), "COMPLETED"),
        "anime_studio": studio,
        "anime_synopsis": strip_html(media.get("description", "")),
        "anime_poster_image_url": a_cov.get("extraLarge") or a_cov.get("large") or "",
        "anime_banner_image_url": media.get("bannerImage") or "",
        "anime_rating_avg": round(a_score / 20, 1) if a_score else "",
        "manga_title": mt.get("english") or mt.get("romaji") or "",
        "manga_original_title": mt.get("native") or mt.get("romaji") or "",
        "manga_status": M_STATUS.get(manga.get("status"), "ONGOING"),
        "manga_description": strip_html(manga.get("description", "")),
        "manga_cover_image_url": m_cov.get("extraLarge") or m_cov.get("large") or "",
        "manga_banner_image_url": manga.get("bannerImage") or "",
        "manga_rating_avg": round(m_score / 20, 1) if m_score else "",
        "genres": ";".join(genres),
        "studio_tag": studio,
    })
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1000)
    ap.add_argument("--per-page", dest="per_page", type=int, default=10)
    ap.add_argument("--out", default="data/works.csv")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    rows, seen = [], set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                for c in COLUMNS:
                    r.setdefault(c, "")
                rows.append(r)
                seen.add((r.get("anime_title") or "").strip())
        print(f"이어하기: 기존 {len(rows)}행")

    page = 1
    while len(rows) < args.count:
        resp = anilist_request({"query": QUERY, "variables": {"page": page, "perPage": args.per_page}})
        if not resp:
            print(f"중단(page {page}): 응답 없음", file=sys.stderr)
            break
        if resp.get("errors"):
            print(f"GraphQL 오류(page {page}): {resp['errors'][:1]} — per-page를 줄여보세요", file=sys.stderr)
            break
        data = (resp.get("data") or {}).get("Page") or {}
        media = data.get("media") or []
        if not media:
            break
        for m in media:
            row = build_row(m)
            if not row or not row["anime_title"]:
                continue
            if row["anime_title"] in seen:
                continue
            seen.add(row["anime_title"])
            rows.append(row)
            if len(rows) >= args.count:
                break
        print(f"  page {page}: 누적 {len(rows)}행")
        with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        if not data.get("pageInfo", {}).get("hasNextPage"):
            break
        page += 1
        time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    manga_set = {r["manga_title"] for r in rows if r["manga_title"]}
    print(f"\n완료 — 애니 {len(rows)}행, 연결된 만화 {len(manga_set)}종. 저장: {args.out}")
    print("다음: python manage.py import_dataset  (1단계 연결 적재)")
    print("그다음: python scripts/enrich_mangaupdates.py  (2단계 회차 매핑)")


if __name__ == "__main__":
    main()

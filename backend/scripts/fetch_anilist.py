"""
AniList GraphQL API로 애니메이션 메타데이터를 수집해 works.csv 를 채운다.

권장 사용 (MangaUpdates 결과에 애니 정보를 덧붙여 완성):
    cd backend
    python scripts/fetch_anilist.py
    # 기본: data/works_from_mangaupdates.csv 를 읽어 애니 열을 채우고 data/works.csv 로 저장

옵션:
    python scripts/fetch_anilist.py --input data/works_from_mangaupdates.csv --out data/works.csv
    python scripts/fetch_anilist.py --titles data/titles.txt --out data/works.csv   # 입력 CSV 없이 새로 생성

특징:
- 429(요청 제한) 시 Retry-After 만큼 기다렸다 자동 재시도.
- 중간에 끊겨도 out 파일을 다시 읽어 '이어서' 진행(이미 채운 행은 건너뜀).
- 공개 데이터, 인증 불필요.

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
query ($search: String) {
  Media(search: $search, type: ANIME) {
    title { romaji english native }
    format
    seasonYear
    startDate { year }
    episodes
    status
    studios(isMain: true) { nodes { name } }
    description(asHtml: false)
    coverImage { extraLarge large }
    bannerImage
    averageScore
    genres
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
STATUS_MAP = {"FINISHED": "COMPLETED", "RELEASING": "ONGOING", "NOT_YET_RELEASED": "UPCOMING", "CANCELLED": "COMPLETED", "HIATUS": "ONGOING"}


def strip_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.I)
    return re.sub(r"<[^>]+>", "", text).strip()


def anilist_request(payload, max_retries=6):
    """429/5xx 자동 재시도. 성공 시 json dict 반환, 실패 시 None."""
    for attempt in range(max_retries):
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=20)
        except requests.RequestException as e:
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
        if r.status_code == 404:
            return {}
        try:
            r.raise_for_status()
        except requests.RequestException:
            return None
        return r.json()
    return None


def fetch_anime(title):
    data = anilist_request({"query": QUERY, "variables": {"search": title}})
    if not data:
        return None
    return (data.get("data") or {}).get("Media")


def fill_anime_columns(row, media):
    t = media.get("title") or {}
    studios = ((media.get("studios") or {}).get("nodes")) or []
    studio = studios[0]["name"] if studios else ""
    year = media.get("seasonYear") or (media.get("startDate") or {}).get("year")
    score = media.get("averageScore")
    cover = media.get("coverImage") or {}
    row["anime_title"] = row.get("anime_title") or t.get("english") or t.get("romaji") or ""
    row["anime_original_title"] = t.get("native") or t.get("romaji") or ""
    row["anime_type"] = FORMAT_MAP.get(media.get("format"), "")
    row["anime_release_year"] = year or ""
    row["anime_episode_count"] = media.get("episodes") or ""
    row["anime_status"] = STATUS_MAP.get(media.get("status"), "COMPLETED")
    row["anime_studio"] = studio
    row["anime_synopsis"] = strip_html(media.get("description", ""))
    row["anime_poster_image_url"] = cover.get("extraLarge") or cover.get("large") or ""
    row["anime_banner_image_url"] = media.get("bannerImage") or ""
    row["anime_rating_avg"] = round(score / 20, 1) if score else ""
    row["studio_tag"] = studio
    existing = [g.strip() for g in (row.get("genres") or "").split(";") if g.strip()]
    for g in media.get("genres") or []:
        if g not in existing:
            existing.append(g)
    row["genres"] = ";".join(existing)
    return row


def search_title_for(row):
    return row.get("anime_title") or row.get("manga_title") or row.get("manga_original_title") or ""


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")
    return rows


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/works_from_mangaupdates.csv")
    ap.add_argument("--titles", default="data/titles.txt")
    ap.add_argument("--out", default="data/works.csv")
    ap.add_argument("--sleep", type=float, default=2.0, help="요청 간 간격(초). 429가 잦으면 늘리세요")
    ap.add_argument("--from", dest="frm", choices=["auto", "titles", "input"], default="auto",
                    help="auto=out/MU/titles 순, titles=titles.txt만(병렬용), input=MU파일")
    args = ap.parse_args()

    def rows_from_titles():
        try:
            with open(args.titles, encoding="utf-8") as f:
                titles = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        except FileNotFoundError:
            print(f"제목 파일 없음: {args.titles}", file=sys.stderr)
            sys.exit(1)
        out = []
        for tt in titles:
            r = {c: "" for c in COLUMNS}
            r["anime_title"] = tt
            out.append(r)
        print(f"입력: {args.titles} ({len(out)}개 제목)")
        return out

    # 이어하기: out 이 이미 있으면 그걸 기준으로 (이미 채운 행은 건너뜀)
    if os.path.exists(args.out):
        rows = read_csv(args.out)
        print(f"이어하기: 기존 {args.out} ({len(rows)}행)에서 미완성 행만 처리")
    elif args.frm == "titles":
        rows = rows_from_titles()
    elif args.frm in ("auto", "input") and os.path.exists(args.input):
        rows = read_csv(args.input)
        print(f"입력: {args.input} ({len(rows)}행)")
    else:
        rows = rows_from_titles()

    ok = fail = skip = 0
    for idx, row in enumerate(rows, 1):
        if row.get("anime_studio") or row.get("anime_episode_count"):
            skip += 1
            continue  # 이미 채워진 행
        title = search_title_for(row)
        if not title:
            continue
        media = fetch_anime(title)
        if not media:
            print(f"  [{idx}/{len(rows)}] 실패: {title}")
            fail += 1
        else:
            fill_anime_columns(row, media)
            ok += 1
            print(f"  [{idx}/{len(rows)}] OK: {title} -> {row['anime_title']}")
            write_csv(args.out, rows)  # 진행 즉시 저장(중단 대비)
        time.sleep(args.sleep)

    write_csv(args.out, rows)
    print(f"\n완료 — 성공 {ok}, 실패 {fail}, 건너뜀 {skip}. 저장: {args.out}")
    print("다음: 매핑(continue_volume/chapter, mapping_text) 검수 후 import_dataset")
    print("데이터 출처 표기 필수: AniList (https://anilist.co)")


if __name__ == "__main__":
    main()

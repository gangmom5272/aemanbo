"""
MangaUpdates 공식 API로 만화 메타데이터를 수집해 works.csv 형식으로 저장.

사용법 (backend/ 에서):
    python scripts/fetch_mangaupdates.py
    python scripts/fetch_mangaupdates.py --titles data/titles.txt --out data/works_from_mangaupdates.csv

- 인증 불필요(공개 데이터). 출처 표기 + 요청 간 간격 준수(이용약관).
- 채우는 열: 만화 메타데이터, 장르, 표지, 평점, 그리고 source_note에 애니화 범위 힌트.
- 애니 메타데이터(제작사/화수/포스터 등)와 최종 매핑(continue_volume/chapter)은
  이후 수동 보강 또는 AniList 수집으로 채웁니다.

데이터 출처: MangaUpdates (https://www.mangaupdates.com)
"""
import argparse
import csv
import re
import sys
import time

import requests

BASE = "https://api.mangaupdates.com/v1"
HEADERS = {"User-Agent": "aemanbo-dataset/1.0", "Content-Type": "application/json"}

# works.csv 와 동일한 헤더 (importer 호환)
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


def strip_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def mu_request(method, url, **kwargs):
    """429/5xx 자동 재시도. 성공 시 Response, 실패 시 None."""
    for attempt in range(6):
        try:
            r = requests.request(method, url, headers=HEADERS, timeout=15, **kwargs)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 30)) + 1
            print(f"    · 429 제한 — {wait}s 대기 후 재시도", flush=True)
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 404:
            return None
        try:
            r.raise_for_status()
        except requests.RequestException:
            return None
        return r
    return None


def search_series(title):
    r = mu_request("POST", f"{BASE}/series/search", json={"search": title, "perpage": 5})
    if not r:
        return None
    results = r.json().get("results", [])
    if not results:
        return None
    return results[0].get("record", {}).get("series_id")


def get_series(series_id):
    r = mu_request("GET", f"{BASE}/series/{series_id}")
    return r.json() if r else None


def to_row(title, rec):
    authors = rec.get("authors", []) or []
    author = next((a["name"] for a in authors if a.get("type") == "Author"), "")
    artist = next((a["name"] for a in authors if a.get("type") == "Artist"), "")
    pubs = rec.get("publishers", []) or []
    publisher = next((p["publisher_name"] for p in pubs if p.get("type") == "Original"), "")
    if not publisher and pubs:
        publisher = pubs[0].get("publisher_name", "")
    genres = ";".join(g.get("genre", "") for g in (rec.get("genres") or []) if g.get("genre"))
    assoc = rec.get("associated") or []
    original_title = assoc[0]["title"] if assoc else ""
    image = ((rec.get("image") or {}).get("url") or {}).get("original", "")
    rating = rec.get("bayesian_rating")
    rating = round(min(float(rating) / 2, 5.0), 1) if rating else ""  # 0-10 -> 0-5 (★ 기준)
    status = "COMPLETED" if rec.get("completed") else "ONGOING"
    anime = rec.get("anime") or {}
    hint = ""
    if anime.get("start") or anime.get("end"):
        hint = f"[MangaUpdates] 애니화 시작: {anime.get('start','?')} / 종료: {anime.get('end','?')}"

    row = {c: "" for c in COLUMNS}
    row.update({
        "manga_title": rec.get("title", title),
        "manga_original_title": original_title,
        "manga_author": author,
        "manga_illustrator": artist,
        "manga_publisher": publisher,
        "manga_status": status,
        "manga_description": strip_html(rec.get("description", "")),
        "manga_cover_image_url": image,
        "manga_rating_avg": rating,
        "genres": genres,
        "source_note": hint,
    })
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", default="data/titles.txt")
    ap.add_argument("--out", default="data/works_from_mangaupdates.csv")
    ap.add_argument("--sleep", type=float, default=1.5, help="요청 간 간격(초)")
    args = ap.parse_args()

    try:
        with open(args.titles, encoding="utf-8") as f:
            titles = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    except FileNotFoundError:
        print(f"제목 파일 없음: {args.titles}", file=sys.stderr)
        sys.exit(1)

    rows, ok, fail = [], 0, 0
    for idx, title in enumerate(titles, 1):
        try:
            sid = search_series(title)
            if not sid:
                print(f"  [{idx}/{len(titles)}] 검색 실패: {title}")
                fail += 1
            else:
                rec = get_series(sid)
                if not rec:
                    print(f"  [{idx}/{len(titles)}] 상세 실패: {title}")
                    fail += 1
                else:
                    rows.append(to_row(title, rec))
                    ok += 1
                    print(f"  [{idx}/{len(titles)}] OK: {title} -> id {sid}")
        except requests.RequestException as e:
            print(f"  [{idx}/{len(titles)}] 오류: {title} ({e})", file=sys.stderr)
            fail += 1
        time.sleep(args.sleep)  # 이용약관: 서버 과부하 방지

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"\n완료 — 성공 {ok}, 실패 {fail}. 저장: {args.out}")
    print("애니 메타데이터/최종 매핑(continue_volume·chapter)은 보강 후 import_dataset 하세요.")
    print("데이터 출처 표기 필수: MangaUpdates (https://www.mangaupdates.com)")


if __name__ == "__main__":
    main()

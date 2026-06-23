"""
works.csv 의 설명/줄거리(anime_synopsis, manga_description)를 한국어로 번역.

  cd backend
  python scripts/translate_dataset.py
  python scripts/translate_dataset.py --in data/works.csv --out data/works.csv --sleep 0.3

- 무료 구글 번역 엔드포인트 사용(키 불필요, 비공식 → 과도하면 일시 차단될 수 있음).
- 이미 한국어인 항목은 건너뜀(이어하기). 번역 실패 시 원문 유지.
- 제목은 번역하지 않음(원문 유지). 적재(import_dataset) 직전에 실행하세요.
"""
import argparse
import csv
import re
import time

import requests

ENDPOINT = "https://translate.googleapis.com/translate_a/single"
FIELDS = ["anime_synopsis", "manga_description"]
HANGUL = re.compile(r"[가-힣]")
LETTER = re.compile(r"[A-Za-z가-힣]")

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


def already_korean(text):
    letters = LETTER.findall(text or "")
    if not letters:
        return True
    ko = sum(1 for ch in letters if HANGUL.match(ch))
    return ko / len(letters) > 0.4


def translate(text):
    q = (text or "").strip()
    if not q:
        return text
    q = q[:1800]
    for attempt in range(4):
        try:
            r = requests.get(
                ENDPOINT,
                params={"client": "gtx", "sl": "auto", "tl": "ko", "dt": "t", "q": q},
                timeout=15,
            )
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            print(f"    · 제한/오류({r.status_code}) — 대기 후 재시도", flush=True)
            time.sleep(3 * (attempt + 1))
            continue
        if not r.ok:
            return None
        try:
            data = r.json()
            return "".join(seg[0] for seg in data[0] if seg and seg[0])
        except Exception:
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/works.csv")
    ap.add_argument("--out", default="data/works.csv")
    ap.add_argument("--sleep", type=float, default=0.3)
    ap.add_argument("--titles", action="store_true", help="일본어 원제 → 한글 제목도 번역")
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")

    done = 0
    skipped = 0
    failed = 0
    for idx, row in enumerate(rows, 1):
        changed = False
        if args.titles:
            for tcol, ocol in (("anime_title", "anime_original_title"), ("manga_title", "manga_original_title")):
                title = (row.get(tcol) or "").strip()
                orig = (row.get(ocol) or "").strip()
                if not title and not orig:
                    continue
                if already_korean(title):  # 이미 한글 제목이면 건너뜀(이어하기)
                    continue
                ko = translate(orig or title)  # 일본어 원제 우선
                if ko:
                    row[tcol] = ko
                    done += 1
                    changed = True
                time.sleep(args.sleep)
        for field in FIELDS:
            val = (row.get(field) or "").strip()
            if not val or already_korean(val):
                skipped += 1
                continue
            ko = translate(val)
            if ko:
                row[field] = ko
                done += 1
                changed = True
            else:
                failed += 1
            time.sleep(args.sleep)
        if changed and idx % 10 == 0:
            with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerows(rows)
            print(f"  [{idx}/{len(rows)}] 번역 누적 {done}", flush=True)

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\n완료 — 번역 {done}, 건너뜀(이미 한국어/빈값) {skipped}, 실패 {failed}. 저장: {args.out}")


if __name__ == "__main__":
    main()

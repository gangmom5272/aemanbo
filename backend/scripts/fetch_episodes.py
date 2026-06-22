"""
AniList 만화 '총 권수(volumes)'를 받아 단행본 목록(episodes.csv)을 생성한다.

  cd backend
  python scripts/fetch_episodes.py                     # works.csv의 만화들 -> episodes.csv
  python scripts/fetch_episodes.py --in data/works.csv --out data/episodes.csv

- 만화마다 volumes(총 권수)를 받아 1권~N권 행을 만듭니다.
- 권별 제목/발매일은 AniList에 없어 비웁니다(번호 위주). chapters(총 화수)는 마지막 권에 메모.
- 429 자동 재시도 + 이어하기(이미 만든 만화는 건너뜀).
- 적재: python manage.py import_dataset (episodes.csv를 자동으로 읽음)

데이터 출처: AniList (https://anilist.co)
"""
import argparse
import csv
import os
import sys
import time

import requests

ENDPOINT = "https://graphql.anilist.co"
QUERY = """
query ($search: String) {
  Media(search: $search, type: MANGA) {
    volumes
    chapters
    title { romaji english }
  }
}
"""
EP_COLUMNS = ["manga_title", "volume_number", "chapter_number", "title", "published_at", "rating_avg"]


def anilist_request(payload, max_retries=6):
    for attempt in range(max_retries):
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=20)
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


def fetch_volumes(title):
    data = anilist_request({"query": QUERY, "variables": {"search": title}})
    if not data:
        return None
    return (data.get("data") or {}).get("Media")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/works.csv")
    ap.add_argument("--out", default="data/episodes.csv")
    ap.add_argument("--sleep", type=float, default=2.0)
    args = ap.parse_args()

    # 대상 만화 제목 모으기
    with open(args.inp, encoding="utf-8-sig", newline="") as f:
        titles = []
        seen = set()
        for r in csv.DictReader(f):
            t = (r.get("manga_title") or "").strip()
            if t and t not in seen:
                seen.add(t)
                titles.append(t)
    print(f"대상 만화 {len(titles)}종")

    # 이어하기: 기존 episodes.csv 에 이미 있는 만화는 건너뜀
    existing_rows = []
    done = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                existing_rows.append(r)
                done.add((r.get("manga_title") or "").strip())
        print(f"이어하기: 기존 {len(done)}종 건너뜀")

    rows = list(existing_rows)
    ok = skip = fail = 0
    for idx, title in enumerate(titles, 1):
        if title in done:
            skip += 1
            continue
        media = fetch_volumes(title)
        vols = (media or {}).get("volumes")
        chaps = (media or {}).get("chapters")
        if not vols:
            print(f"  [{idx}/{len(titles)}] 권수 없음: {title}")
            fail += 1
        else:
            for v in range(1, int(vols) + 1):
                rows.append({
                    "manga_title": title,
                    "volume_number": v,
                    "chapter_number": "",
                    "title": "",
                    "published_at": "",
                    "rating_avg": "",
                })
            # 마지막 권에 총 화수 메모(있으면)
            if chaps:
                rows[-1]["title"] = f"(완결까지 총 {chaps}화)"
            ok += 1
            print(f"  [{idx}/{len(titles)}] OK: {title} -> {vols}권")
            # 진행 즉시 저장(중단 대비)
            with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=EP_COLUMNS)
                w.writeheader()
                w.writerows(rows)
        time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EP_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\n완료 — 생성 {ok}종, 건너뜀 {skip}, 권수없음 {fail}. 저장: {args.out}")
    print("다음: python manage.py import_dataset")


if __name__ == "__main__":
    main()

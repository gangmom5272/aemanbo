"""
AniList 인기순으로 제목 목록을 자동 생성해 data/titles.txt 로 저장.

사용법 (backend/ 에서):
    python scripts/gen_titles.py                  # 인기 만화 1000개
    python scripts/gen_titles.py --count 500
    python scripts/gen_titles.py --type ANIME     # 인기 애니 기준
    python scripts/gen_titles.py --out data/titles.txt

- 기본은 인기 '만화'(format MANGA) 기준. 원작 만화가 있는 작품이라 매핑에 적합.
- 중복 자동 제거. AniList 공개 데이터, 인증 불필요(분당 ~90요청).

데이터 출처: AniList (https://anilist.co)
"""
import argparse
import sys
import time

import requests

ENDPOINT = "https://graphql.anilist.co"
QUERY = """
query ($page: Int, $type: MediaType, $format: MediaFormat, $source: MediaSource) {
  Page(page: $page, perPage: 50) {
    pageInfo { hasNextPage }
    media(type: $type, format: $format, source: $source, sort: POPULARITY_DESC, isAdult: false) {
      title { romaji english }
    }
  }
}
"""


def anilist_request(payload, max_retries=6):
    for attempt in range(max_retries):
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=20)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 60)) + 1
            print(f"  · 429 제한 — {wait}s 대기 후 재시도", flush=True)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1000)
    ap.add_argument("--type", choices=["MANGA", "ANIME"], default="MANGA")
    ap.add_argument("--out", default="data/titles.txt")
    ap.add_argument("--no-manga-source", dest="manga_source", action="store_false",
                    help="(ANIME 모드) 원작=만화 제한을 끔. 기본은 켜짐")
    ap.set_defaults(manga_source=True)
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    fmt = "MANGA" if args.type == "MANGA" else "TV"
    titles, seen = [], set()
    page = 1
    while len(titles) < args.count:
        # 애니 모드: 원작이 '만화'인 작품만 (애니+만화 둘 다 있는 작품)
        source = "MANGA" if (args.type == "ANIME" and args.manga_source) else None
        variables = {"page": page, "type": args.type, "format": fmt, "source": source}
        resp = anilist_request({"query": QUERY, "variables": variables})
        if not resp:
            print(f"오류(page {page}): 응답 없음, 중단", file=sys.stderr)
            break
        data = (resp.get("data") or {}).get("Page") or {}
        media = data.get("media") or []
        if not media:
            break
        for m in media:
            t = m.get("title") or {}
            name = t.get("english") or t.get("romaji")
            if name and name not in seen:
                seen.add(name)
                titles.append(name)
                if len(titles) >= args.count:
                    break
        print(f"  page {page}: 누적 {len(titles)}개")
        if not data.get("pageInfo", {}).get("hasNextPage"):
            break
        page += 1
        time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# AniList 인기 {args.type} 상위 {len(titles)}개 (자동 생성)\n")
        f.write("# 출처: AniList (https://anilist.co)\n")
        for name in titles:
            f.write(name + "\n")

    print(f"\n완료 — {len(titles)}개 저장: {args.out}")


if __name__ == "__main__":
    main()

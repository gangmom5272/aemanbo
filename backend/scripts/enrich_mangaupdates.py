"""
[2단계] MangaUpdates로 '애니 회차 ↔ 만화 권/화'를 채운다. (시즌 번호 기반 매칭)

  cd backend
  python scripts/enrich_mangaupdates.py

전제: 1단계(collect_anilist.py)로 애니↔만화 연결이 끝난 works.csv.

매칭 방식:
- MangaUpdates의 애니화 구간 라벨(S1, S3P1, S4P1...)에서 '시즌 번호'를 추출.
- AniList 애니 제목(Season 3, Final Season, 3rd Season...)에서도 '시즌 번호'를 추출.
- 같은 시즌끼리 연결 → 파트(S3 / S3 Part 2)가 같은 시즌 구간을 공유, 어긋남 방지.
- 라벨이 전혀 없으면 연도순 1:1(차선책)으로 폴백.
- 빈 칸만 채움. 429 자동 재시도 + 이어하기.

데이터 출처: MangaUpdates (https://www.mangaupdates.com)
"""
import argparse
import csv
import re
import time

import requests

BASE = "https://api.mangaupdates.com/v1"
HEADERS = {"User-Agent": "aemanbo-dataset/1.0", "Content-Type": "application/json"}
# "Vol 1, Chap 1 (S1)" -> (vol, chap, label)
ENTRY_RE = re.compile(r"Vol\s*(\d+)\s*,\s*Chap\s*(\d+)\s*(?:\(([^)]*)\))?", re.I)
SEASON_IN_LABEL = re.compile(r"S(\d+)", re.I)

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


def g(r, k):
    return (r.get(k) or "").strip()


def to_int(v, d=0):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return d


def mu_request(method, url, **kwargs):
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


def parse_entries(s):
    """'Vol X, Chap Y (Sn..)' 나열 -> [(vol, chap, season_or_None)]"""
    out = []
    for v, c, label in ENTRY_RE.findall(s or ""):
        sm = SEASON_IN_LABEL.search(label or "")
        season = int(sm.group(1)) if sm else None
        out.append((int(v), int(c), season))
    return out


def fetch_series(title):
    """MangaUpdates 작품 정보(작가/그림작가/출판사) + 애니화 구간을 함께 반환. 시리즈 못 찾으면 None."""
    r = mu_request("POST", f"{BASE}/series/search", json={"search": title, "perpage": 5})
    if not r:
        return None
    results = r.json().get("results", [])
    if not results:
        return None
    sid = results[0].get("record", {}).get("series_id")
    if not sid:
        return None
    r2 = mu_request("GET", f"{BASE}/series/{sid}")
    if not r2:
        return None
    rec = r2.json() or {}

    authors = rec.get("authors") or []
    author = next((a.get("name", "") for a in authors if a.get("type") == "Author"), "")
    illustrator = next((a.get("name", "") for a in authors if a.get("type") == "Artist"), "")
    if not author and authors:
        author = authors[0].get("name", "")
    pubs = rec.get("publishers") or []
    publisher = next((p.get("publisher_name", "") for p in pubs if p.get("type") == "Original"), "")
    if not publisher and pubs:
        publisher = pubs[0].get("publisher_name", "")

    anime = rec.get("anime") or {}
    start_s, end_s = anime.get("start") or "", anime.get("end") or ""
    starts, ends = parse_entries(start_s), parse_entries(end_s)
    hint = (
        f"[MangaUpdates] 애니화 시작: {start_s} / 종료: {end_s}"
        if (start_s or end_s)
        else "[MangaUpdates] 메타데이터"
    )
    return {
        "starts": starts,
        "ends": ends,
        "hint": hint,
        "author": author,
        "illustrator": illustrator,
        "publisher": publisher,
    }


ANI_SEASON = re.compile(r"season\s*(\d+)|(\d+)(?:st|nd|rd|th)\s+season", re.I)


def anime_season_num(title, max_season):
    t = (title or "").lower()
    m = ANI_SEASON.search(t)
    if m:
        return int(m.group(1) or m.group(2))
    if "final season" in t or "the final" in t:
        return max_season  # 파이널 = 마지막 시즌
    return 1  # 시즌 표기 없으면 1기


def fill_episodes(row):
    if not g(row, "anime_episode_from"):
        row["anime_episode_from"] = "1"
    if not g(row, "anime_episode_to") and g(row, "anime_episode_count"):
        row["anime_episode_to"] = g(row, "anime_episode_count")


def apply_range(row, sv, sc, ev, ec, all_starts):
    cont_chap = ec + 1
    cont_vol = ev
    for v, c, _ in all_starts:
        if c == cont_chap:
            cont_vol = v
            break
    if not g(row, "manga_volume_from"):
        row["manga_volume_from"] = str(sv)
    if not g(row, "manga_chapter_from"):
        row["manga_chapter_from"] = str(sc)
    if not g(row, "manga_volume_to"):
        row["manga_volume_to"] = str(ev)
    if not g(row, "manga_chapter_to"):
        row["manga_chapter_to"] = str(ec)
    if not g(row, "continue_volume"):
        row["continue_volume"] = str(cont_vol)
    if not g(row, "continue_chapter"):
        row["continue_chapter"] = str(cont_chap)
    if not g(row, "mapping_text"):
        row["mapping_text"] = f"애니 시청 후 원작 {cont_vol}권 {cont_chap}화부터"


def assign(group, hint):
    starts, ends, htext = hint["starts"], hint["ends"], hint["hint"]
    pairs = list(zip(starts, ends))  # 구간 i = (start_i, end_i)
    for r in group:
        if not g(r, "source_note"):
            r["source_note"] = htext
        fill_episodes(r)

    # 시즌 라벨이 충분하면 '시즌 번호' 매칭, 아니면 연도순 1:1 폴백
    season_of_pair = [s[2] for s, _ in pairs]
    have_labels = sum(1 for x in season_of_pair if x) >= max(1, len(pairs) - 1)

    group_sorted = sorted(group, key=lambda r: (to_int(g(r, "anime_release_year"), 9999),
                                                to_int(g(r, "anime_episode_count")),
                                                g(r, "anime_title")))
    if have_labels:
        max_season = max([x for x in season_of_pair if x] or [1])
        by_season = {}
        for (sv, sc, sseason), (ev, ec, _) in pairs:
            key = sseason if sseason else None
            if key is not None:
                by_season[key] = (sv, sc, ev, ec)
        for r in group:
            sn = anime_season_num(g(r, "anime_title"), max_season)
            rng = by_season.get(sn)
            if rng:
                apply_range(r, rng[0], rng[1], rng[2], rng[3], starts)
    else:
        # 폴백: 연도순으로 구간을 순서대로 매칭
        for i, r in enumerate(group_sorted):
            if i < len(pairs):
                (sv, sc, _), (ev, ec, _) = pairs[i]
                apply_range(r, sv, sc, ev, ec, starts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/works.csv")
    ap.add_argument("--out", default="data/works.csv")
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")

    groups = {}
    for r in rows:
        mt = g(r, "manga_title")
        if mt and g(r, "anime_title"):
            groups.setdefault(mt, []).append(r)

    print(f"보강 대상 만화 {len(groups)}종 / 전체 {len(rows)}행")
    ok = miss = skip = 0
    for idx, (mt, grp) in enumerate(groups.items(), 1):
        if all("[MangaUpdates]" in g(r, "source_note") for r in grp):
            skip += 1
            continue
        info = fetch_series(mt)
        if not info:
            for r in grp:
                fill_episodes(r)
            print(f"  [{idx}/{len(groups)}] 작품 못 찾음: {mt}")
            miss += 1
        else:
            # 작품 정보(작가/그림작가/출판사) 채우기 — 빈 칸만
            for r in grp:
                if not g(r, "manga_author") and info["author"]:
                    r["manga_author"] = info["author"]
                if not g(r, "manga_illustrator") and info["illustrator"]:
                    r["manga_illustrator"] = info["illustrator"]
                if not g(r, "manga_publisher") and info["publisher"]:
                    r["manga_publisher"] = info["publisher"]
            # 회차 매핑 (애니화 구간이 있을 때만)
            if info["starts"] and info["ends"]:
                assign(grp, info)
                mapped = sum(1 for r in grp if g(r, "continue_chapter"))
                print(f"  [{idx}/{len(groups)}] OK: {mt} (구간 {len(info['starts'])}, 애니 {len(grp)}, 매핑 {mapped})")
            else:
                for r in grp:
                    fill_episodes(r)
                    if not g(r, "source_note"):
                        r["source_note"] = info["hint"]
                print(f"  [{idx}/{len(groups)}] 정보만: {mt} (애니화 구간 없음)")
            ok += 1
            with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerows(rows)
        time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\n완료 — 보강 {ok}종, 힌트없음 {miss}, 건너뜀 {skip}. 저장: {args.out}")


if __name__ == "__main__":
    main()

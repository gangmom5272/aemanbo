# -*- coding: utf-8 -*-
"""
이어보기 지점이 비어 있는 매핑대상 작품을 MangaUpdates에서 조회해
'사용가능 / 화만가능 / 불가' 로 자동 분류하고, 추천 이어보기 지점을 뽑아준다.

동작:
  1) MangaUpdates 검색 API(POST)로 만화 원제(없으면 한글 제목)로 시리즈를 찾고
  2) 시리즈 상세 API(GET)에서 anime.start / anime.end 를 읽어
  3) 분류 + 이어보기 권/화(1기 기준)를 계산해 CSV로 저장

사용법:
  cd backend
  python scripts/classify_continue.py \
      --mapping "이어보기_매핑대상_제외후_2차.csv" \
      --works data/works_fixed.csv \
      --out 이어보기_분류결과.csv

필요: requests (pip install requests)
"""
import argparse
import csv
import re
import sys
import time

import requests

API = "https://api.mangaupdates.com/v1"
HEADERS = {"User-Agent": "aemanbo-classifier/1.0", "Content-Type": "application/json"}


def read_csv(path):
    raw = open(path, "rb").read().replace(b"\x00", b"")
    txt = raw.decode("utf-8-sig", "replace")
    rows = list(csv.reader(txt.splitlines()))
    header = [c.strip().lstrip("﻿") for c in rows[0]]
    data = [r for r in rows[1:] if len(r) == len(header)]
    return header, data


def search_series(title):
    """제목으로 MU 시리즈 검색 → (series_id, mu_title, mu_url) 또는 None."""
    try:
        r = requests.post(
            f"{API}/series/search",
            json={"search": title, "page": 1, "perpage": 5},
            headers=HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            return None
        rec = results[0].get("record") or {}
        return rec.get("series_id"), rec.get("title"), rec.get("url")
    except Exception as e:
        print(f"  [검색오류] {title}: {e}", file=sys.stderr)
        return None


def get_series(series_id):
    try:
        r = requests.get(f"{API}/series/{series_id}", headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [상세오류] {series_id}: {e}", file=sys.stderr)
        return None


SEG_RE = re.compile(r"(?:Vol\s*(\d+)\s*,\s*)?Chap\s*([0-9.]+)", re.I)


def parse_point(text):
    """'Vol 6, Chap 29 (S1) / Vol 7, Chap 30 (S2)' → [(vol|None, chap), ...] 세그먼트 리스트."""
    if not text:
        return []
    pts = []
    for seg in str(text).split("/"):
        m = SEG_RE.search(seg)
        if m:
            vol = int(m.group(1)) if m.group(1) else None
            pts.append((vol, m.group(2)))
    return pts


def classify(anime):
    """anime={start,end} → (분류, 이어보기권, 이어보기화, 비고)."""
    start = (anime or {}).get("start")
    end = (anime or {}).get("end")
    note_bits = []
    low = f"{start} {end}".lower()
    if any(k in low for k in ["alternate", "different", "abridged", "original ending"]):
        note_bits.append("원작과 전개 차이 있음(검토 권장)")

    end_pts = parse_point(end)
    start_pts = parse_point(start)

    # 종료점이 전혀 없으면 불가
    if not end_pts:
        return "불가", "", "", (end or "종료점 없음")

    # 1기 기준 이어보기 지점:
    #  - start 에 2번째(S2) 세그먼트가 있으면 그게 곧 이어볼 지점
    #  - 없으면 end 1기의 다음 화
    if len(start_pts) >= 2:
        cv, cc = start_pts[1]
    else:
        ev, ec = end_pts[0]
        try:
            cc = str(int(float(ec)) + 1)
        except ValueError:
            cc = ec
        cv = ev

    has_vol = cv is not None
    if has_vol:
        cls = "사용가능"
    else:
        cls = "화만가능"
        note_bits.append("웹툰 등 권(volume) 정보 없음")

    return cls, (str(cv) if cv is not None else ""), str(cc), " / ".join(note_bits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True, help="매핑대상 CSV (애니제목/방영연도/만화제목/이어보기권/이어보기화 포함)")
    ap.add_argument("--works", default="", help="원제 보강용 works CSV (anime_title/anime_release_year/manga_original_title)")
    ap.add_argument("--out", default="이어보기_분류결과.csv")
    ap.add_argument("--sleep", type=float, default=0.7, help="요청 간 대기(초)")
    args = ap.parse_args()

    mh, md = read_csv(args.mapping)

    def mi(n):
        return mh.index(n)

    # 컬럼 자동 인식: 검수대상_136(연도/만화원제) 와 매핑대상(방영연도/이어보기권/화) 둘 다 지원
    at = mi("애니제목")
    yr = mi("방영연도") if "방영연도" in mh else mi("연도")
    mt = mi("만화제목")
    orig_col = mh.index("만화원제") if "만화원제" in mh else -1
    has_cont = ("이어보기권" in mh) and ("이어보기화" in mh)
    cv_i = mi("이어보기권") if has_cont else -1
    cc_i = mi("이어보기화") if has_cont else -1

    # 원제 보강(파일에 만화원제가 없을 때만 works CSV 사용)
    orig = {}
    if orig_col < 0 and args.works:
        wh, wd = read_csv(args.works)
        wat, wyr = wh.index("anime_title"), wh.index("anime_release_year")
        wmo = wh.index("manga_original_title")
        for r in wd:
            orig[(r[wat].strip(), r[wyr].strip())] = r[wmo].strip()

    # 이어보기 컬럼이 있으면 비어있는 행만, 없으면(이미 검수대상 목록) 전체가 대상
    if has_cont:
        targets = [r for r in md if not (r[cv_i].strip() or r[cc_i].strip())]
    else:
        targets = md
    print(f"검수 대상: {len(targets)}개")

    out_rows = []
    counts = {"사용가능": 0, "화만가능": 0, "불가": 0, "검색실패": 0}
    for n, r in enumerate(targets, 1):
        anime_t, year, manga_t = r[at].strip(), r[yr].strip(), r[mt].strip()
        if orig_col >= 0:
            query = r[orig_col].strip() or manga_t
        else:
            query = orig.get((anime_t, year), "") or manga_t
        print(f"[{n}/{len(targets)}] {anime_t} ← 검색:{query}")

        found = search_series(query)
        if not found and query != manga_t:
            found = search_series(manga_t)  # 원제 실패 시 한글로 재시도

        if not found:
            counts["검색실패"] += 1
            out_rows.append([anime_t, year, manga_t, "", "", "", "", "검색실패", "", "", "MU에서 시리즈 못 찾음"])
            time.sleep(args.sleep)
            continue

        sid, mu_title, mu_url = found
        detail = get_series(sid)
        anime = (detail or {}).get("anime") or {}
        cls, ccv, ccc, note = classify(anime)
        counts[cls] = counts.get(cls, 0) + 1
        out_rows.append([
            anime_t, year, manga_t, mu_title or "", mu_url or "",
            (anime.get("start") or ""), (anime.get("end") or ""),
            cls, ccv, ccc, note,
        ])
        time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["애니제목", "방영연도", "만화제목", "MU제목", "MU_URL",
                    "anime_start", "anime_end", "분류", "추천이어보기권", "추천이어보기화", "비고"])
        w.writerows(out_rows)

    print("\n=== 분류 요약 ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\n저장: {args.out}")


if __name__ == "__main__":
    main()

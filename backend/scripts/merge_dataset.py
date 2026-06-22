"""
따로 수집한 두 CSV(만화 / 애니)를 한 파일(works.csv)로 합친다.

병렬 워크플로:
    # 터미널 1
    python scripts/fetch_mangaupdates.py                                   # -> works_from_mangaupdates.csv
    # 터미널 2 (동시에)
    python scripts/fetch_anilist.py --from titles --out data/works_from_anilist.csv
    # 둘 다 끝나면
    python scripts/merge_dataset.py                                        # -> works.csv
    python manage.py import_dataset

합치는 기준(--by):
  index (기본) : 두 파일 + titles.txt 의 행 수가 같을 때, 같은 순서로 1:1 결합 (정확).
                 MangaUpdates가 일부 실패해 행 수가 다르면 중단하고 알려줌.
  title        : 제목 정규화 후 매칭 (행 수가 안 맞을 때의 차선책, 일부 누락 가능).
"""
import argparse
import csv
import os
import re
import sys

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
ANIME_COLS = [c for c in COLUMNS if c.startswith("anime_")] + ["studio_tag"]
MANGA_COLS = [c for c in COLUMNS if c.startswith("manga_")]


def norm(t):
    return re.sub(r"[^0-9a-z가-힣]+", "", (t or "").lower())


def read(path):
    if not os.path.exists(path):
        print(f"파일 없음: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS:
            if r.get(c) is None:
                r[c] = ""
    return rows


def merge_genres(a, b):
    out = []
    for g in [x.strip() for x in (a or "").split(";")] + [x.strip() for x in (b or "").split(";")]:
        if g and g not in out:
            out.append(g)
    return ";".join(out)


def combine(anime_row, manga_row):
    row = {c: "" for c in COLUMNS}
    if anime_row:
        for c in ANIME_COLS:
            row[c] = anime_row.get(c, "")
    if manga_row:
        for c in MANGA_COLS:
            row[c] = manga_row.get(c, "")
        row["source_note"] = manga_row.get("source_note", "")
    a_g = anime_row.get("genres", "") if anime_row else ""
    m_g = manga_row.get("genres", "") if manga_row else ""
    row["genres"] = merge_genres(a_g, m_g)
    return row


def count_titles(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return sum(1 for ln in f if ln.strip() and not ln.startswith("#"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anime", default="data/works_from_anilist.csv")
    ap.add_argument("--manga", default="data/works_from_mangaupdates.csv")
    ap.add_argument("--titles", default="data/titles.txt")
    ap.add_argument("--out", default="data/works.csv")
    ap.add_argument("--by", choices=["index", "title"], default="index")
    args = ap.parse_args()

    anime = read(args.anime)
    manga = read(args.manga)
    n_titles = count_titles(args.titles)
    print(f"애니 {len(anime)}행, 만화 {len(manga)}행" + (f", 제목 {n_titles}개" if n_titles else ""))

    merged = []
    if args.by == "index":
        if len(anime) != len(manga):
            print(
                "\n[중단] 두 파일의 행 수가 다릅니다 — index 결합은 순서가 어긋날 수 있어요.\n"
                "  · 한쪽 수집에서 실패가 있었을 가능성이 큽니다.\n"
                "  · 해결: 실패한 쪽을 다시 돌려 행 수를 맞추거나,  --by title 로 시도하거나,\n"
                "          가장 안전한 방법은 chained 방식(rm works.csv 후 fetch_anilist 단독) 입니다.",
                file=sys.stderr,
            )
            sys.exit(1)
        for a, m in zip(anime, manga):
            merged.append(combine(a, m))
        print(f"index 결합 완료: {len(merged)}행")
    else:  # title — 제목/원제(원어) 여러 키로 매칭
        def keys(row, fields):
            ks = set()
            for f in fields:
                k = norm(row.get(f))
                if k:
                    ks.add(k)
            return ks

        idx = {}
        for m in manga:
            for k in keys(m, ["manga_title", "manga_original_title"]):
                idx.setdefault(k, m)
        used, unmatched = set(), 0
        for a in anime:
            m = None
            for k in keys(a, ["anime_title", "anime_original_title"]):
                if k in idx:
                    m = idx[k]
                    break
            if m:
                used.add(id(m))
            else:
                unmatched += 1
            merged.append(combine(a, m))
        # 애니와 못 맞춘 만화는 만화-only 행으로 보존
        manga_only = 0
        for m in manga:
            if id(m) not in used:
                merged.append(combine(None, m))
                manga_only += 1
        print(f"title 결합 완료: {len(merged)}행 (애니에 만화 미매칭 {unmatched}, 만화-only {manga_only})")

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(merged)
    print(f"저장: {args.out}")
    print("다음: 매핑(continue_volume/chapter, mapping_text) 검수 후  python manage.py import_dataset")


if __name__ == "__main__":
    main()

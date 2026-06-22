"""
source_note 의 MangaUpdates 애니화 힌트를 파싱해 회차 매핑 칼럼을 채운다.

  python scripts/fill_mapping.py
  python scripts/fill_mapping.py --in data/works.csv --out data/works.csv

채우는 칼럼(비어 있을 때만):
  anime_episode_from=1, anime_episode_to=애니 화수,
  manga_volume_from/chapter_from = 첫 시작 지점,
  manga_volume_to/chapter_to     = 1기 종료 지점,
  continue_volume/continue_chapter = 종료 다음 화(이어보기),
  mapping_text = "애니 시청 후 원작 N권 M화부터"

힌트 형식 예:
  [MangaUpdates] 애니화 시작: Vol 1, Chap 1 (S1) / Vol 9, Chap 35 (S2) ...
                 / 종료: Vol 8, Chap 34 (S1 + OVA 1) / Vol 12, Chap 50 (S2) ...
* 매칭된 애니는 보통 1기이므로 '첫 시작 ~ 첫 종료'(S1 범위)를 사용합니다.
* 이어보기 권수는 가능하면 '종료+1화'와 같은 시작 항목의 권수를 찾아 맞춥니다.
* 자동 채움이라 최종 검수는 권장합니다.
"""
import argparse
import csv
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

PAIR_RE = re.compile(r"Vol\s*(\d+)\s*,\s*Chap\s*(\d+)", re.I)


def parse_hint(note):
    """returns dict with start/end/all_starts or None"""
    if not note or "시작" not in note:
        return None
    parts = re.split(r"종료\s*[:：]", note, maxsplit=1)
    start_part, end_part = parts[0], (parts[1] if len(parts) > 1 else "")
    starts = [(int(v), int(c)) for v, c in PAIR_RE.findall(start_part)]
    ends = [(int(v), int(c)) for v, c in PAIR_RE.findall(end_part)]
    if not starts or not ends:
        return None
    return {"starts": starts, "ends": ends}


def fill_row(row):
    def g(k):
        return (row.get(k) or "").strip()

    if not (g("anime_title") and g("manga_title")):
        return False

    # 애니 회차: 1 ~ 화수
    if not g("anime_episode_from"):
        row["anime_episode_from"] = "1"
    if not g("anime_episode_to") and g("anime_episode_count"):
        row["anime_episode_to"] = g("anime_episode_count")

    hint = parse_hint(g("source_note"))
    if not hint:
        return False

    sv, sc = hint["starts"][0]      # 첫 시작 (보통 1기 시작)
    ev, ec = hint["ends"][0]        # 첫 종료 (1기 종료)
    cont_chap = ec + 1
    # 이어보기 권수: 종료+1화와 같은 시작 항목이 있으면 그 권수 사용
    cont_vol = ev
    for v, c in hint["starts"]:
        if c == cont_chap:
            cont_vol = v
            break

    if not g("manga_volume_from"):
        row["manga_volume_from"] = str(sv)
    if not g("manga_chapter_from"):
        row["manga_chapter_from"] = str(sc)
    if not g("manga_volume_to"):
        row["manga_volume_to"] = str(ev)
    if not g("manga_chapter_to"):
        row["manga_chapter_to"] = str(ec)
    if not g("continue_volume"):
        row["continue_volume"] = str(cont_vol)
    if not g("continue_chapter"):
        row["continue_chapter"] = str(cont_chap)
    if not g("mapping_text"):
        row["mapping_text"] = f"애니 시청 후 원작 {cont_vol}권 {cont_chap}화부터"
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/works.csv")
    ap.add_argument("--out", default="data/works.csv")
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")

    filled = sum(1 for r in rows if fill_row(r))

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"회차 매핑 채움: {filled}행 / 전체 {len(rows)}행")
    print(f"저장: {args.out}")
    print("다음: python manage.py import_dataset (검수 권장)")


if __name__ == "__main__":
    main()

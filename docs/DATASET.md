# 데이터셋 구축 가이드

애만보의 핵심은 **애니 ↔ 원작 만화 매핑** 데이터입니다.
메타데이터는 외부 API로 자동 수집하고, 매핑(이어보기 지점)은 사람이 검수해 채웁니다.

## 전체 흐름

```
(⓪ gen_titles.py 로 자동 생성 가능)
titles.txt (제목 목록)
   │  ① MangaUpdates 수집 (만화 메타 + 애니화 범위 힌트)
   ▼
data/works_from_mangaupdates.csv
   │  ② AniList 수집 (애니 제작사·화수·연도·포스터 자동 채움)
   ▼
data/works.csv
   │  ③ 매핑(continue_volume/chapter, mapping_text) 수동 검수
   │  ④ 임포터
   ▼
SQLite DB  →  /admin 에서 검수/수정
```

> ①→② 를 거치면 만화·애니 메타데이터가 대부분 자동으로 채워지고,
> 사람이 직접 할 일은 사실상 **매핑 검수(③)** 만 남습니다.

## ⓪ 제목 목록 생성 (AniList 인기순)

직접 제목을 적어도 되지만, 인기순 1000개를 자동으로 받아올 수 있습니다.

```bash
cd backend
python scripts/gen_titles.py                # 인기 만화 1000개 -> data/titles.txt
python scripts/gen_titles.py --count 500    # 개수 지정
python scripts/gen_titles.py --type ANIME   # 인기 애니 기준
```

- 기본은 인기 '만화' 기준(원작이 있어 매핑에 적합), 중복 자동 제거.
- 출처 표기 필수: AniList.

## ① 메타데이터 수집 (MangaUpdates)

`backend/data/titles.txt` 에 만화 제목을 한 줄씩 적고(영문 제목이 매칭이 잘 됩니다) 실행:

```bash
cd backend
python scripts/fetch_mangaupdates.py
# 결과: data/works_from_mangaupdates.csv
```

- MangaUpdates 공식 API(`https://api.mangaupdates.com/v1`) 사용, 인증 불필요.
- 채워지는 항목: 만화 제목/원제/작가/그림작가/출판사/상태/설명/표지/평점/장르,
  그리고 `source_note` 에 **애니화 시작·종료 범위 힌트**(매핑 작성의 출발점).
- 이용약관 준수: 요청 간 간격 유지(기본 1.5초), **출처 표기 필수**(MangaUpdates).

> MangaUpdates는 만화 중심이라 애니 제작사/화수/포스터는 제공되지 않습니다.
> 애니 메타데이터는 AniList(https://graphql.anilist.co) 또는 Jikan으로 보강하거나 수동 입력하세요.

## ② 애니 메타데이터 수집 (AniList)

①의 결과에 애니 정보를 자동으로 덧붙입니다.

```bash
cd backend
python scripts/fetch_anilist.py
# 기본: data/works_from_mangaupdates.csv 를 읽어 애니 열을 채우고 data/works.csv 로 저장
```

- AniList GraphQL API(`https://graphql.anilist.co`) 사용, 인증 불필요.
- 채워지는 항목: 애니 제목/원제/유형/연도/화수/상태/제작사/줄거리/포스터·배너/평점, 장르 보강.
- 평점은 양쪽 모두 **★ 5점 스케일**로 통일됩니다.
- 출처 표기 필수: AniList.

## ③ 매핑 검수 (수동, 가장 중요)

`data/works.csv` 를 열어(엑셀은 **UTF-8 CSV로 저장**) `source_note` 의 애니화 범위 힌트를 보고 채웁니다:
  - `anime_season_label, anime_episode_from~to`
  - `manga_volume_from~to, manga_chapter_from~to`
  - `continue_volume, continue_chapter` ← 애니 다음에 이어볼 지점
  - `mapping_text` ← 화면 표시 문구 (예: "애니 1기 이후 원작 만화 8권 64화부터")

완성되면 `data/works.csv` 로 저장합니다. 단행본 목록이 있으면 `data/episodes.csv` 도 채웁니다.

## (대안) 병렬 수집 후 합치기

MangaUpdates와 AniList는 서로 다른 서버라 **동시에 돌려도 됩니다.** 단, 각자 다른 파일에 쓰고 마지막에 합칩니다.

```bash
# 터미널 1
python scripts/fetch_mangaupdates.py                                    # -> works_from_mangaupdates.csv
# 터미널 2 (동시에)
python scripts/fetch_anilist.py --from titles --out data/works_from_anilist.csv
# 둘 다 끝나면 합치기
python scripts/merge_dataset.py                                         # -> works.csv
```

- `merge_dataset.py --by index`(기본): 두 파일 행 수가 같으면 같은 순서로 정확히 1:1 결합.
  한쪽에 수집 실패가 있어 행 수가 다르면 중단하고 알려줍니다.
- `--by title`: 제목 정규화 매칭(차선책, 일부 누락 가능).
- 가장 안전한 짝맞춤이 필요하면 순차(chained) 방식(① → ②)을 쓰세요.

## ④ 적재 (임포터)

```bash
cd backend
python manage.py migrate
python manage.py import_dataset            # data/works.csv + data/episodes.csv
# 또는 경로 지정
python manage.py import_dataset --works data/works.csv --episodes data/episodes.csv
```

- 모든 적재는 `update_or_create` 기반 → 여러 번 실행해도 중복 없이 갱신.
- 적재 후 `http://127.0.0.1:8000/admin` 에서 매핑 누락/이미지 깨짐을 검수합니다.

## works.csv 컬럼 요약

| 그룹 | 컬럼 |
| --- | --- |
| 애니 | anime_title, anime_original_title, anime_type, anime_release_year, anime_episode_count, anime_status, anime_studio, anime_synopsis, anime_poster_image_url, anime_banner_image_url, anime_rating_avg, anime_rating_count, anime_favorite_count |
| 만화 | manga_title, manga_original_title, manga_author, manga_illustrator, manga_publisher, manga_status, manga_description, manga_cover_image_url, manga_banner_image_url, manga_rating_avg, manga_rating_count, manga_favorite_count |
| 태그 | genres(`;`로 구분), studio_tag |
| 매핑 | anime_season_label, anime_episode_from, anime_episode_to, manga_volume_from, manga_volume_to, manga_chapter_from, manga_chapter_to, continue_volume, continue_chapter, mapping_text, mapping_description, source_note |

## 빠른 테스트용 목 데이터

실제 데이터셋과 별개로, 기능 확인용 샘플은 아래로 즉시 채울 수 있습니다.

```bash
python manage.py seed_demo   # 작품 5쌍 + 데모유저(demo/demo1234) + 찜/댓글
```

## 데이터 출처 표기

- 만화 메타데이터: **MangaUpdates** (https://www.mangaupdates.com)
- 애니 메타데이터: **AniList** (https://anilist.co) / **Jikan·MyAnimeList**
서비스 화면 또는 안내에 출처를 명시하세요(각 API 이용약관).

# 애니 보고 만화 보고 (애만보) — 기획·설계 명세서 v2

애니메이션 ↔ 원작 만화 연동 정보 및 추천 플랫폼

> 본 문서는 최초 기획안(`PROJECT_SPEC.md`)을 기반으로, 개발 과정에서 추가·확장된 기능과
> 구체화된 설계를 반영한 **확장판 기획안**입니다.

---

# 1. 프로젝트 개요

| 항목 | 내용 |
| --- | --- |
| 서비스명 | 애니 보고 만화 보고 (애만보) |
| 서비스 유형 | 서브컬처 메타데이터 유틸리티 & 커뮤니티 플랫폼 |
| 핵심 가치 | 애니 시청 후 **원작 만화를 몇 권 몇 화부터** 봐야 하는지 즉시 해결 |
| 포지셔닝 | 직접 스트리밍 없이 공식 PV 임베드 + 정교한 매핑 데이터 + AI 추천 |

## 1.1 서비스 컨셉

애만보는 애니메이션 시청 후 원작 만화를 이어서 보고 싶은 사용자의 니즈를 해결하는 매핑 데이터 플랫폼이다.
직접 영상 스트리밍은 제공하지 않고, 공식 프로모션 영상(PV/트레일러) 임베드와 정교한 메타데이터
(애니↔만화 매핑, 장르, 제작사, 에피소드 정보)에 집중하여 저작권 리스크를 줄인 서브컬처 유틸리티로 포지셔닝한다.

## 1.2 핵심 도메인

- **애니↔만화 연결 정보**: 애니를 본 뒤 원작 만화를 어디서부터 이어 보면 되는지(권/화) 제공
- **작품 상세 정보**: 애니/만화 상세, 시즌별 매핑, 미디어(PV/OP/ED)
- **사용자 저장 및 활동**: 찜하기, 댓글, 마이페이지
- **AI 추천 및 챗봇**: 취향·자연어 기반 추천과 매핑 질의응답
- **개인화**: 선호 장르 기반 추천

---

# 2. 주요 기능 명세

> ⭐ 표시는 최초 기획안 이후 **추가·확장된 기능**.

## A. 메인 홈 및 탐색

- 글로벌 통합 검색: 애니/만화 제목 검색 (제목·원제 기준, 오타 허용 퍼지 매칭)
- ⭐ **자연어/설명 검색 폴백**: 제목 검색이 0건일 때 ① 줄거리·장르 DB 검색 → ② LLM이 DB 작품 목록에서 직접 선택해 추천 ("도깨비" 같은 키워드/설명으로도 작품 탐색)
- ⭐ **오늘의 랜덤 픽**: 인기순 고정이 아닌 랜덤 추천 카드(새로고침 시 변경) — 로그인 시 **선호 장르 우선** 노출
- AI 챗봇 추천 진입(플로팅 FAB)

## B. 작품 상세 및 매핑 정보

- 통합 매핑 인디케이터: `애니 1기 → 원작 만화 N권 M화부터` 브릿지 UI
- 시즌별 이어보기 모달: 한 만화에 연결된 여러 애니 시즌을 방영 연도순으로 정렬해 표시(애니 포스터 포함)
- 애니↔만화 상호 이동(원작 만화 보기 / 애니 정보 보기), 포스터 표시
- 합법적 미디어: 공식 PV/OP/ED를 YouTube 검색 링크로 연결
- 찜하기(하트)
- ⭐ **관리자 인라인 편집**: 관리자 계정으로 상세 페이지에서 제목·원제·줄거리를 즉시 수정(DB 반영)

## C. AI 챗봇 추천 (3차)

- 플로팅 챗봇, 자연어 추천, **DB 근거 클릭형 추천 카드**
- "부드러운 큐레이터" 페르소나(정중한 존댓말, 작품마다 어울리는 이유 한 줄)
- OpenAI(SSAFY GMS 프록시) 사용, 세션 기반 대화 문맥 유지

## D. 커뮤니티 및 사용자 상호작용

- 작품별 댓글 CRUD(작성/수정/삭제, 닉네임 표시, 소프트 삭제)
- 소셜 로그인: 구글 / 카카오 / 네이버
- 로그아웃, CSRF 부트스트랩

## E. 마이페이지 및 활동 기록

- 유저 프로필(닉네임·프로필 사진 업로드, 기본 닉네임 = 이메일)
- 찜한 콘텐츠, 나의 활동(댓글 이력, 삭제 댓글 숨김)
- ⭐ **선호 장르 편집**(설문에서 고른 장르를 마이페이지에서 변경)

## F. ⭐ 개인화 온보딩 (신규)

- 첫 소셜 로그인 시 **선호 장르 설문 모달**(복수 선택, 건너뛰기 가능)
- 선택 결과로 홈 "오늘의 랜덤 픽"을 개인화(선호 장르 우선 + 부족 시 일반 랜덤)

## G. ⭐ 관리자 기능 (신규/고도화)

- 작품 제목/원제/줄거리 인라인 수정(role=ADMIN 전용 PATCH API)
- 장르 한글화 표시(영문 장르명 → 한글), 비장르 태그(스튜디오 등) 숨김

---

# 3. 기획 이후 추가·확장 요약 (하이라이트)

| # | 추가 기능 | 설명 | 가치 |
| --- | --- | --- | --- |
| 1 | 선호 장르 온보딩 | 첫 로그인 설문 → 홈 추천 개인화 | 신규 사용자 즉시 개인화 |
| 2 | 자연어/설명 검색 폴백 | 제목 0건 시 줄거리·장르 검색 → LLM이 DB에서 선택 | 검색 실패율↓, 발견성↑ |
| 3 | 관리자 인라인 편집 | 상세 페이지에서 제목·원제·줄거리 즉시 수정 | 데이터 품질 운영 효율 |
| 4 | 이어보기 데이터 검수 파이프라인 | MangaUpdates `anime.start/end` 자동 분류(사용가능/화만/불가) | 매핑 신뢰도 확보 |
| 5 | 장르 한글화 | 영문 장르 → 한글, 비장르 태그 숨김 | UX·가독성 |
| 6 | 오늘의 랜덤 픽 | 인기순 → 랜덤 + 선호 장르 반영 | 탐색 재미·다양성 |

## 변경(축소)된 항목

- **단행본(manga_episodes) 기능 제거**: 데이터 확보가 어렵고 가치가 작아 도메인에서 제외
- 추천 매핑을 "인기순"에서 **랜덤 픽 + 개인화**로 변경
- 데이터 소스를 "수동 시드"에서 **AniList + MangaUpdates 자동 수집 + 번역 + 수동 검수 파이프라인**으로 구체화

---

# 4. 기술 스택 및 아키텍처

| 분류 | 기술 |
| --- | --- |
| Frontend | Vue 3 (Vite, vue-router) SPA |
| Backend | Python / Django 5 + DRF (세션 인증) |
| Database | SQLite(개발) → PostgreSQL(배포) |
| 인증 | OAuth 소셜 로그인(구글/카카오/네이버), 세션 기반 |
| LLM | OpenAI(gpt-4o-mini) — SSAFY GMS 프록시 경유 |
| 메타데이터 수집 | AniList GraphQL(애니↔만화 관계·메타), MangaUpdates API(이어보기 지점) |
| 영상 | YouTube 검색 링크 임베드 |

### 앱 구성(백엔드)

- `apps.works` — 작품/매핑/태그, 검색, 추천, 관리자 수정
- `apps.users` — 회원/소셜계정/프로필/선호장르/온보딩
- `apps.interactions` — 찜/댓글
- `apps.chat` — AI 챗봇 + 자연어 검색 폴백

---

# 5. 데이터 구축 파이프라인 ⭐

애만보의 핵심은 **애니↔만화 매핑(이어보기 지점)** 데이터다. 메타데이터는 자동 수집, 매핑은 검수로 채운다.

```
gen_titles.py (AniList 인기작 제목 생성)
   │ ① collect_anilist.py  : 애니 + relations로 원작 만화 연결, 메타 자동 채움
   ▼
   │ ② enrich_mangaupdates.py : 작가/출판사 + 애니화 범위 힌트
   ▼
   │ ③ translate_dataset.py : 줄거리/제목 한글화(기계번역 + 검수)
   ▼
data/works.csv  (1행 = 애니 + 원작 만화 + 매핑 + 태그)
   │ ④ classify_continue.py : MangaUpdates anime.start/end → 이어보기 지점
   │                          '사용가능 / 화만가능 / 불가' 자동 분류
   ▼
   │ ⑤ import_dataset --fresh : DB 적재(중복 방지)
   ▼
SQLite DB  →  관리자 인라인 편집/검수
```

- 전체 **약 1,000개 매핑** 구축, 이어보기 지점 **892개** 확보(사용가능 + 화만가능)
- 검수 불가/제외(극장판·OVA·단편 등)는 매핑만 유지하고 이어보기 지점은 비움
- 줄거리 한글화 및 메타데이터 혼입·오역 정리, 제목 오역 일괄 교정

---

# 6. 구현 우선순위 및 현황

| 단계 | 범위 | 상태 |
| --- | --- | --- |
| 1차 MVP | 홈/추천 매핑, 통합 검색, 애니/만화 상세, 애니↔만화 정보 | ✅ 완료 |
| 2차 MVP | 소셜 로그인, 찜, 마이페이지, 프로필 | ✅ 완료 |
| 3차 | 댓글 CRUD, 나의 활동, AI 챗봇, 관리자 고도화 | ✅ 완료 |
| 확장 | 선호 장르 온보딩, 자연어 검색 폴백, 관리자 인라인 편집, 이어보기 검수 | ✅ 완료 |

---

# 7. 데이터베이스 설계 (핵심 테이블)

- `animes`, `mangas` — 작품 메타데이터 (※ `manga_episodes`는 제거)
- `anime_manga_mappings` — 애니↔만화 연결 + **이어보기 지점**(continue_volume/chapter, mapping_text)
- `metadata_tags`, `anime_tags`, `manga_tags` — 장르/태그/제작사 N:M (GENRE/TAG/STUDIO)
- `users`(+ `preferred_genres`, `onboarded`, `role`), `social_accounts`, `favorites`
- `anime_comments`, `manga_comments` — 댓글(소프트 삭제)

### anime_manga_mappings 핵심 필드

- `manga_volume_from/to`, `manga_chapter_from/to` — 애니가 다룬 원작 범위
- `continue_volume`, `continue_chapter` — **이어볼 지점**(권/화)
- `mapping_text` — `애니 시청 후 원작 N권 M화부터` 안내 문구
- `source_note` — 출처/근거(MangaUpdates 등)

---

# 8. 화면별 API 요약 (⭐ = 신규)

## 홈 / 검색
- `GET /api/v1/home/`
- `GET /api/v1/search/?keyword=`
- `GET /api/v1/mappings/recommendations/`
- ⭐ `POST /api/v1/search/ai/` — 자연어/설명 검색 폴백
- ⭐ `GET /api/v1/genres/` — 장르 목록(설문/필터용)

## 인증 / 프로필
- `GET /api/v1/auth/oauth/{provider}/url/` · `.../callback/`
- `POST /api/v1/auth/logout/` · `GET /api/v1/auth/session/` · `GET /api/v1/auth/csrf/`
- `GET/PATCH /api/v1/users/me/profile/` (⭐ `preferred_genres`, `onboarded` 포함)
- `POST /api/v1/users/me/avatar/`

## 애니 / 만화 상세
- `GET /api/v1/animes/{id}/` · ⭐ `PATCH /api/v1/animes/{id}/` (관리자 수정)
- `GET /api/v1/animes/{id}/manga-mappings/` · `.../comments/`
- `GET /api/v1/mangas/{id}/` · ⭐ `PATCH /api/v1/mangas/{id}/` (관리자 수정)
- `GET /api/v1/mangas/{id}/anime-mappings/` · `.../comments/`

## 찜 / 마이페이지
- `POST /api/v1/favorites/` · `DELETE /api/v1/favorites/{id}/`
- `GET /api/v1/users/me/favorites/` · `.../comments/`

## AI 챗봇
- `POST /api/v1/chat/message/` · `DELETE /api/v1/chat/session/`

---

> 본 문서는 `docs/PROJECT_SPEC.md`(최초 기획안)와 `docs/IMPLEMENTATION_SPEC.md`(구현 명세),
> `docs/DATASET.md`(데이터 가이드)를 토대로, 개발 과정에서의 추가·변경을 반영한 v2 기획안이다.

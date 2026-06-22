# 애니 보고 만화 보고

애니메이션-원작 만화 연동 정보 및 추천 플랫폼

**프로젝트 기획 및 설계 명세서**

---

# 1. 프로젝트 개요

| 항목 | 내용 |
| --- | --- |
| 서비스명 | 애니 보고 만화 보고 |
| 서비스 유형 | 서브컬처 메타데이터 유틸리티 & 커뮤니티 플랫폼 |
| 핵심 가치 | 애니 시청 후 원작 만화 몇 화부터 봐야 하는지 즉시 해결 |
| 포지셔닝 | 직접 스트리밍 없이 공식 PV 임베드 + 정교한 매핑 데이터 제공 |

## 1.1 서비스 컨셉

애니 보고 만화 보고는 애니메이션 시청 후 원작 만화를 이어서 보고 싶은 사용자의 니즈를 해결하는 매핑 데이터 플랫폼입니다.

직접 영상 스트리밍 기능은 제공하지 않고, 공식 프로모션 영상(PV/트레일러) 임베드와 정교한 메타데이터(애니-만화 매핑, 장르, 제작사, 에피소드 정보)에 집중하여 저작권 리스크를 줄인 서브컬처 유틸리티 서비스로 포지셔닝합니다.

## 1.2 핵심 도메인

- 애니와 만화의 연결 정보: 애니를 본 뒤 원작 만화를 어디서부터 이어 보면 되는지 제공
- 작품 상세 정보: 애니/만화 상세, 에피소드 목록, 미디어(PV, OP, ED)
- 사용자 저장 및 활동 기능: 찜하기, 관심작품 등록, 댓글
- AI 추천 및 챗봇: 취향 기반 추천과 매핑 정보 질의응답

---

# 2. 주요 기능 명세

## A. 메인 홈 및 탐색

- 글로벌 통합 검색: 애니메이션, 만화 작품명 및 매핑 정보를 한 번에 검색
- 메타데이터 기반 필터링: 장르, 태그, 제작사 기준 탐색
- 추천 매핑 정보 큐레이션: `애니 X기 -> 원작 만화 Y권 Z화부터` 형태의 카드형 UI 제공
- AI 애니 추천 진입 버튼: 자연어 입력 기반 맞춤 작품 및 매핑 정보 반환

## B. 작품 상세 및 매핑 정보

- 통합 매핑 인디케이터: `애니 1기 -> 만화 1~4권` 형태의 직관적인 브릿지 UI
- 애니 정보 보기 / 만화 정보 보기 상호 이동 버튼
- 합법적 미디어 제공: 공식 PV, OP, ED를 YouTube iFrame으로 임베드
- 에피소드/단행본 리스트: 회차별 평점, 방영일/발행일, 줄거리 제공
- 찜하기 / 공유하기 기능

## C. AI 챗봇 추천 시스템 (3차)

- 플로팅 챗봇, 자연어 추천, 작품별 챗봇, OpenAI API, 세션/캐시 기반 대화 문맥 유지

## D. 커뮤니티 및 사용자 상호작용

- 작품/에피소드별 댓글, 대댓글, 소셜 로그인(구글/카카오/네이버)

## E. 마이페이지 및 활동 기록

- 유저 프로필, 찜한 콘텐츠, 콘텐츠 상태 뱃지, 나의 활동 이력

---

# 3. 기술 스택 및 아키텍처

| 분류 | 기술 |
| --- | --- |
| Frontend | Vue.js (SPA) |
| Backend | Python / Django + DRF |
| Database | SQLite -> PostgreSQL |
| LLM API | OpenAI API |
| 영상 데이터 | YouTube Data API v3 |
| 만화 데이터 | 수동 시드 데이터 + 외부 참고 데이터 |

---

# 4. MVP 구현 우선순위

- **1차 MVP**: 홈/추천 매핑, 통합 검색, 애니/만화 상세, 애니↔만화 정보 보기
- **2차 MVP**: 소셜 로그인, 찜/관심작품, 마이페이지, 프로필
- **3차**: 댓글/대댓글, 나의 활동, 미디어 확장, AI 챗봇, 관리자 고도화

---

# 5. 데이터베이스 설계 (핵심 테이블)

- `animes`, `mangas`, `manga_episodes` — 작품/단행본 메타데이터
- `anime_manga_mappings` — 애니↔만화 연결 핵심 브릿지 테이블
- `metadata_tags`, `anime_tags`, `manga_tags` — 장르/태그/제작사 N:M
- `users`, `social_accounts`, `favorites` — 회원/소셜/찜
- `anime_comments`, `manga_comments` — 댓글(소프트 삭제)

### anime_manga_mappings 예시

- `애니 1기: 원작 코믹스 1~5권`
- `애니 2기 이후: 원작 만화 8권 45화부터`

---

# 7. 화면별 API 호출 요약

## 홈
- GET /api/v1/home
- GET /api/v1/search?keyword=
- GET /api/v1/mappings/recommendations

## 로그인
- GET /api/v1/auth/oauth/{provider}/url
- GET /api/v1/auth/oauth/{provider}/callback
- POST /api/v1/auth/logout

## 애니 상세
- GET /api/v1/animes/{animeId}
- GET /api/v1/animes/{animeId}/manga-mappings
- GET /api/v1/animes/{animeId}/media        (3차)
- GET/POST /api/v1/animes/{animeId}/comments
- POST /api/v1/favorites · DELETE /api/v1/favorites/{favoriteId}

## 만화 상세
- GET /api/v1/mangas/{mangaId}
- GET /api/v1/mangas/{mangaId}/episodes
- GET /api/v1/mangas/{mangaId}/anime-mappings
- GET/POST /api/v1/mangas/{mangaId}/comments

## 마이페이지
- GET/PATCH /api/v1/users/me/profile
- GET /api/v1/users/me/favorites
- GET /api/v1/users/me/comments

## AI 챗봇 (3차)
- POST /api/v1/chat/message
- DELETE /api/v1/chat/session

---

> 본 문서는 원본 저장소(gangmom5272/aemanbo)의 docs/PROJECT_SPEC.md 요약본입니다.
> 전체 기획서와 docs/IMPLEMENTATION_SPEC.md는 GitHub 저장소에서 확인할 수 있습니다.

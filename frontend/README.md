# 애만보 Frontend (Vue 3 + Vite)

프로토타입 디자인을 그대로 옮긴 Vue 3 SPA입니다. Django(DRF) 백엔드 API와 연결됩니다.

## 실행

```sh
npm install
npm run dev
```

- 개발 서버: http://localhost:5173
- `/api` 요청은 `vite.config.js`의 프록시로 Django(`http://127.0.0.1:8000`)에 전달됩니다.
  같은 출처로 동작하므로 세션 쿠키 인증이 그대로 유지됩니다.

## 환경변수

`.env.example` 참고. 기본값으로 충분합니다.

```
VITE_API_BASE=/api/v1
```

## 구조

```
src/
  api/
    client.js     # fetch 래퍼 (credentials 포함, CSRF 토큰 자동 첨부)
    index.js      # 엔드포인트 함수 모음 (구현/미구현 구분 주석)
  router/index.js # 라우팅
  utils/          # 커버 그라데이션, YouTube 링크 헬퍼
  components/     # 헤더/푸터/FAB/작품카드
  views/          # 홈/리스트/검색/상세/마이/로그인 화면
```

## 백엔드 연동 현황

연결 완료 (백엔드 구현됨):
- 홈 `/home/`, 검색 `/search/`, 추천매핑 `/mappings/recommendations/`
- 애니/만화 상세, 매핑, 단행본
- 찜 `/favorites/`, 내 찜/댓글 `/users/me/...`
- 댓글 조회/작성
- OAuth 로그인 URL/콜백/세션/로그아웃, 프로필

URL만 잡아둔 미구현(백엔드 추후 작업) — `src/api/index.js` 하단 참고:
- 전체 목록 `GET /api/v1/animes/`, `GET /api/v1/mangas/`
  (현재는 실패 시 홈의 인기 목록으로 임시 폴백)
- 공식 영상 `GET /api/v1/animes/:id/media/` (현재는 YouTube 검색 링크로 대체)
- AI 챗봇 `POST /api/v1/chat/message/` (FAB 클릭 시 안내만)

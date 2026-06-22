# 애만보 (애니 보고 만화 보고)

애니메이션 시청 후 원작 만화를 어디서부터 보면 되는지 알려주는 애니-만화 매핑 플랫폼.

- **backend/** — Django 5.2 + DRF (SQLite)
- **frontend/** — Vue 3 + Vite SPA
- **docs/** — 기획/구현 명세

## 빠른 시작

### 1) 백엔드

```sh
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_works        # 샘플 애니/만화/매핑 시드
python manage.py createsuperuser   # (선택) 관리자 계정 → /admin
python manage.py runserver         # http://127.0.0.1:8000
```

### 2) 프론트엔드 (새 터미널)

```sh
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

브라우저에서 http://localhost:5173 접속. `/api` 요청은 Vite 프록시로 Django에 전달됩니다.

## 소셜 로그인 (선택)

`backend/`에서 환경변수로 OAuth 키를 설정하면 카카오/네이버/구글 로그인이 동작합니다.
미설정 시 로그인 버튼은 "키 미설정" 안내를 표시합니다.

```
GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
KAKAO_CLIENT_ID  / KAKAO_CLIENT_SECRET
NAVER_CLIENT_ID  / NAVER_CLIENT_SECRET
```

## 미구현(프론트에 URL만 연결됨, 백엔드 추후 작업)

- 전체 애니/만화 목록 API → 현재 인기 목록으로 임시 폴백
- 애니 공식 영상(PV/OP/ED) API → YouTube 검색 링크로 대체
- AI 추천 챗봇 API

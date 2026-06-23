import { api, getCookie, API_BASE, ApiError } from './client'

// CSRF 쿠키 발급 (앱 시작 시 1회 호출 → 이후 POST/PATCH에 토큰 사용)
export const getCsrf = () => api.get('/auth/csrf/')

// 프로필 사진 업로드 (multipart)
export async function uploadAvatar(file) {
  const fd = new FormData()
  fd.append('image', file)
  const csrf = getCookie('csrftoken')
  const res = await fetch(`${API_BASE}/users/me/avatar/`, {
    method: 'POST',
    body: fd,
    credentials: 'include',
    headers: csrf ? { 'X-CSRFToken': csrf } : {},
  })
  const text = await res.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!res.ok) throw new ApiError((data && data.detail) || res.statusText, res.status, data)
  return data
}

// ──────────────────────────────────────────────
// 구현 완료된 백엔드 API
// ──────────────────────────────────────────────

// 홈 (추천 매핑 + 인기 애니/만화)
export const getHome = () => api.get('/home/')

// 통합 검색
export const search = (keyword) => api.get('/search/', { keyword })

// 추천 매핑 더보기
export const getRecommendedMappings = (limit = 20) =>
  api.get('/mappings/recommendations/', { limit })

// 애니 상세 / 매핑 / 댓글
export const getAnime = (id) => api.get(`/animes/${id}/`)
export const getAnimeMangaMappings = (id) => api.get(`/animes/${id}/manga-mappings/`)
export const getAnimeComments = (id) => api.get(`/animes/${id}/comments/`)
export const postAnimeComment = (id, content) =>
  api.post(`/animes/${id}/comments/`, { content })
export const deleteAnimeComment = (animeId, commentId) =>
  api.delete(`/animes/${animeId}/comments/${commentId}/`)
export const patchAnimeComment = (animeId, commentId, content) =>
  api.patch(`/animes/${animeId}/comments/${commentId}/`, { content })

// 만화 상세 / 단행본 / 매핑 / 댓글
export const getManga = (id) => api.get(`/mangas/${id}/`)
export const getMangaAnimeMappings = (id) => api.get(`/mangas/${id}/anime-mappings/`)
export const getMangaComments = (id) => api.get(`/mangas/${id}/comments/`)
export const postMangaComment = (id, content) =>
  api.post(`/mangas/${id}/comments/`, { content })
export const deleteMangaComment = (mangaId, commentId) =>
  api.delete(`/mangas/${mangaId}/comments/${commentId}/`)
export const patchMangaComment = (mangaId, commentId, content) =>
  api.patch(`/mangas/${mangaId}/comments/${commentId}/`, { content })

// 찜 / 관심작품
export const addFavorite = (targetType, targetId, statusLabel = '') =>
  api.post('/favorites/', { target_type: targetType, target_id: targetId, status_label: statusLabel })
export const removeFavorite = (favoriteId) => api.delete(`/favorites/${favoriteId}/`)
export const getMyFavorites = () => api.get('/users/me/favorites/')
export const getMyComments = () => api.get('/users/me/comments/')

// 인증 / 프로필
export const getSession = () => api.get('/auth/session/')
export const logout = () => api.post('/auth/logout/')
export const getOAuthUrl = (provider) => api.get(`/auth/oauth/${provider}/url/`)
export const oauthCallback = (provider, code) =>
  api.get(`/auth/oauth/${provider}/callback/`, { code })
export const getMyProfile = () => api.get('/users/me/profile/')
export const updateMyProfile = (payload) => api.patch('/users/me/profile/', payload)

// ──────────────────────────────────────────────
// 아직 백엔드 미구현 — URL만 잡아둠 (백엔드 추후 작업)
// 호출부에서 실패 시 graceful fallback 처리
// ──────────────────────────────────────────────

// 전체 애니 목록 (정렬/장르 필터). TODO: backend GET /api/v1/animes/
export const listAnimes = (params) => api.get('/animes/', params)
// 전체 만화 목록. TODO: backend GET /api/v1/mangas/
export const listMangas = (params) => api.get('/mangas/', params)
// 애니 공식 영상(PV/OP/ED). TODO: backend GET /api/v1/animes/:id/media/
export const getAnimeMedia = (id) => api.get(`/animes/${id}/media/`)
// AI 추천 챗봇
export const sendChatMessage = (message) => api.post('/chat/message/', { message })
export const clearChatSession = () => api.delete('/chat/session/')

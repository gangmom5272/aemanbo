// 공통 API 클라이언트 (fetch 래퍼)
// Vite dev 서버가 /api 요청을 Django(127.0.0.1:8000)로 프록시하므로
// 같은 출처로 동작 -> 세션 쿠키 인증이 그대로 유지됩니다.
export const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const BASE = API_BASE

export function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return match ? decodeURIComponent(match.pop()) : ''
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function request(path, { method = 'GET', body, params } = {}) {
  let url = BASE + path
  if (params) {
    const usp = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
    )
    const qs = usp.toString()
    if (qs) url += '?' + qs
  }

  const headers = {}
  const options = { method, headers, credentials: 'include' }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }
  if (!['GET', 'HEAD'].includes(method)) {
    const csrf = getCookie('csrftoken')
    if (csrf) headers['X-CSRFToken'] = csrf
  }

  const res = await fetch(url, options)

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const detail = (data && data.detail) || res.statusText
    throw new ApiError(detail, res.status, data)
  }
  return data
}

export const api = {
  get: (path, params) => request(path, { method: 'GET', params }),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}

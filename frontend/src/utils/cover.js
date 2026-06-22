// 작품 커버 placeholder: 제목 기반 결정적 그라데이션 생성 + 상태 라벨 헬퍼
const ANIME_PALETTE = [
  ['#5B2BD6', '#9D3CE0', '#2D6BD4'],
  ['#0E7A5F', '#15B886', '#0BA0B5'],
  ['#C0341E', '#FF6A2C', '#E01E62'],
  ['#1E2A78', '#3B4FD6', '#6A3CE0'],
  ['#8A1F2E', '#E0432E', '#F0843C'],
  ['#A1206E', '#FF4DA6', '#7A40E0'],
  ['#0E5AA8', '#2DA7D6', '#3AC7C0'],
  ['#C95A1E', '#F0A93B', '#13B5A0'],
]
const MANGA_COLORS = [
  '#7C4DEF', '#0E7A5F', '#E0432E', '#3B4FD6', '#FF6A2C',
  '#F0843C', '#5A6678', '#2DA7D6', '#A1206E', '#5A3A2E',
]

function hash(str) {
  let h = 0
  for (let i = 0; i < (str || '').length; i++) {
    h = (h * 31 + str.charCodeAt(i)) >>> 0
  }
  return h
}

export function animeGradient(title) {
  const p = ANIME_PALETTE[hash(title) % ANIME_PALETTE.length]
  return `linear-gradient(150deg,${p[0]},${p[1]} 55%,${p[2]})`
}

export function mangaColor(title) {
  return MANGA_COLORS[hash(title) % MANGA_COLORS.length]
}

// 실제 이미지 URL이 유효해 보이면 사용, 아니면 null (그라데이션 사용)
export function realImage(url) {
  if (!url) return null
  if (url.includes('example.com')) return null // 시드 placeholder 제외
  return url
}

// status(ONGOING/COMPLETED/UPCOMING) -> 배지 클래스/라벨
export function statusBadge(status) {
  switch (status) {
    case 'COMPLETED':
      return { cls: 'done', label: '완결' }
    case 'UPCOMING':
      return { cls: 'new', label: 'UPCOMING' }
    case 'ONGOING':
    default:
      return { cls: 'on', label: '연재중' }
  }
}

export function animeStatusBadge(status) {
  if (status === 'COMPLETED') return { cls: 'done', label: '완결' }
  if (status === 'UPCOMING') return { cls: 'new', label: '방영예정' }
  return { cls: 'on', label: '방영중' }
}

export function ratingText(value) {
  const n = Number(value || 0)
  return n.toFixed(1)
}

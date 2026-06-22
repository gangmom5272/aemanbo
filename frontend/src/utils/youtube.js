// 공식 영상은 백엔드 미구현이므로 제목 기반 YouTube 검색 링크로 연결 (프로토타입과 동일)
export function ytSearch(title, kind) {
  const q = `${title} ${kind}`.trim()
  return 'https://www.youtube.com/results?search_query=' + encodeURIComponent(q)
}

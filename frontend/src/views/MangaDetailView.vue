<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getManga, getMangaAnimeMappings, getMangaComments, postMangaComment, deleteMangaComment, patchMangaComment, addFavorite, removeFavorite, getMyFavorites, getSession } from '../api'
import { animeGradient, mangaColor, realImage, ratingText } from '../utils/cover'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()

const loading = ref(true)
const notFound = ref(false)
const manga = ref(null)
const mappings = ref([])
const comments = ref([])
const newComment = ref('')
const favId = ref(null)
const posting = ref(false)
const showAnimeModal = ref(false)
const myUserId = ref(null)
const editingId = ref(null)
const editText = ref('')

async function refreshComments() {
  const r = await getMangaComments(manga.value.id)
  comments.value = r.results || []
}
async function removeComment(c) {
  if (!confirm('이 댓글을 삭제할까요?')) return
  try {
    await deleteMangaComment(manga.value.id, c.id)
    await refreshComments()
  } catch (e) {
    alert('삭제에 실패했어요.')
  }
}
function startEdit(c) {
  editingId.value = c.id
  editText.value = c.content
}
function cancelEdit() {
  editingId.value = null
  editText.value = ''
}
async function saveEdit(c) {
  const content = editText.value.trim()
  if (!content) return
  try {
    await patchMangaComment(manga.value.id, c.id, content)
    cancelEdit()
    await refreshComments()
  } catch (e) {
    alert('수정에 실패했어요.')
  }
}

function goAnime(id) {
  showAnimeModal.value = false
  router.push({ name: 'anime-detail', params: { id } })
}

const band = computed(() => (manga.value ? mangaColor(manga.value.title) : '#7C4DEF'))
const cover = computed(() => realImage(manga.value?.cover_image_url))
// 연결된 애니 매핑을 만화 진행 순(권/화)으로 정렬해 전부 표시
const sortedMappings = computed(() =>
  [...mappings.value].sort((a, b) => {
    const av = (a.manga_volume_from || 0) * 100000 + (a.manga_chapter_from || 0)
    const bv = (b.manga_volume_from || 0) * 100000 + (b.manga_chapter_from || 0)
    return av - bv
  })
)

function rangeText(m) {
  if (!m) return ''
  const vf = m.manga_volume_from, vt = m.manga_volume_to, cf = m.manga_chapter_from, ct = m.manga_chapter_to
  if (vf && vt) return `${vf}권 ~ ${vt}권${ct ? ' ' + ct + '화' : ''}`
  if (cf && ct) return `${cf}화 ~ ${ct}화`
  return m.mapping_text
}

async function toggleFavorite() {
  if (!manga.value) return
  try {
    if (favId.value) { await removeFavorite(favId.value); favId.value = null }
    else { const fav = await addFavorite('MANGA', manga.value.id); favId.value = fav.id }
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      if (confirm('관심작품 등록은 로그인이 필요해요. 로그인할까요?')) router.push('/login')
    } else alert('처리 중 오류가 발생했어요.')
  }
}

async function submitComment() {
  const content = newComment.value.trim()
  if (!content || posting.value) return
  posting.value = true
  try {
    await postMangaComment(manga.value.id, content)
    newComment.value = ''
    const c = await getMangaComments(manga.value.id)
    comments.value = c.results || []
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      if (confirm('댓글을 남기려면 로그인이 필요해요. 로그인할까요?')) router.push('/login')
    } else alert('댓글 등록에 실패했어요.')
  } finally {
    posting.value = false
  }
}

onMounted(async () => {
  try {
    manga.value = await getManga(props.id)
    const [mp, cm] = await Promise.allSettled([
      getMangaAnimeMappings(props.id),
      getMangaComments(props.id),
    ])
    if (mp.status === 'fulfilled') mappings.value = mp.value.mappings || []
    if (cm.status === 'fulfilled') comments.value = cm.value.results || []
    // 이미 찜한 작품이면 버튼 상태 반영 (비로그인은 무시)
    try {
      const s = await getSession()
      if (s.authenticated) {
        myUserId.value = s.user?.id
        const favs = await getMyFavorites()
        const f = (favs.results || []).find((x) => x.target_type === 'MANGA' && x.target_id === manga.value.id)
        if (f) favId.value = f.id
      }
    } catch (_) { /* 무시 */ }
  } catch (e) {
    notFound.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="wrap">
    <div v-if="loading" class="state-msg">불러오는 중…</div>
    <div v-else-if="notFound" class="state-msg"><div class="big">작품을 찾을 수 없어요</div><RouterLink to="/manga" style="color:var(--spot-deep)">만화 목록으로</RouterLink></div>

    <template v-else>
      <div class="crumb">
        <RouterLink to="/">홈</RouterLink><span class="sep">/</span>
        <RouterLink to="/manga">만화</RouterLink><span class="sep">/</span>
        <span class="cur">{{ manga.title }}</span>
      </div>

      <div class="dhero manga">
        <div class="banner"><div class="bg"></div><div class="scrim"></div></div>
        <div class="body">
          <div class="poster cv-manga">
            <img v-if="cover" class="real" :src="cover" :alt="manga.title" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:1" />
            <span class="ribbon">코믹스</span>
            <span class="pt">{{ manga.title }}</span>
          </div>
          <div class="headinfo">
            <span class="kind manga">● 만화 · 원작</span>
            <h1>{{ manga.title }}</h1>
            <div v-if="manga.original_title" class="orig">{{ manga.original_title }}</div>
            <div class="metarow">
              <span v-if="manga.author" class="chip">작가 <b>{{ manga.author }}</b></span>
              <span v-if="manga.illustrator" class="chip">그림 <b>{{ manga.illustrator }}</b></span>
              <span v-if="manga.publisher" class="chip">출판 <b>{{ manga.publisher }}</b></span>
              <span v-if="manga.status === 'COMPLETED'" class="chip status-done">완결</span>
              <span v-else class="chip">연재중</span>
            </div>
            <div class="statline">
              <div class="rate"><span class="star">★</span><span class="num">{{ ratingText(manga.rating_avg) }}</span><span class="cnt">{{ manga.rating_count }}명 평가</span></div>
              <div class="actions">
                <button class="btn" :class="{ active: favId }" :aria-label="favId ? '찜 취소' : '찜하기'" @click="toggleFavorite">{{ favId ? '♥' : '♡' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-body">
        <!-- 작품 소개 -->
        <div v-if="manga.description" class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>작품 소개</h2></div>
          <p class="prose">{{ manga.description }}</p>
          <div v-if="manga.tags && manga.tags.length" class="tags">
            <span v-for="t in manga.tags" :key="t.id" class="tag"><span class="h">#</span>{{ t.name }}</span>
          </div>
        </div>

        <!-- 애니 매핑 (애니 상세의 map-strip 디자인과 통일, 클릭 시 모달) -->
        <div v-if="sortedMappings.length" class="map-strip" style="cursor:pointer" @click="showAnimeModal = true">
          <div class="ms-cover cv-anime" :style="{ background: animeGradient(sortedMappings[0].anime?.title || manga.title) }"></div>
          <div class="ms-main">
            <div class="ms-label">📺 원작을 봤다면, <b>이 작품의 애니는</b></div>
            <div class="ms-coord">{{ sortedMappings.length }}개 시즌<small>이어보기 매핑 보기</small></div>
          </div>
          <button class="ms-cta" @click.stop="showAnimeModal = true">
            애니 보기
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </button>
        </div>

        <!-- 작품 정보 -->
        <div class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>작품 정보</h2></div>
          <div class="infogrid">
            <div v-if="manga.original_title" class="ig"><span class="k">원제</span><span class="v">{{ manga.original_title }}</span></div>
            <div v-if="manga.author" class="ig"><span class="k">작가</span><span class="v">{{ manga.author }}</span></div>
            <div v-if="manga.illustrator" class="ig"><span class="k">그림</span><span class="v">{{ manga.illustrator }}</span></div>
            <div v-if="manga.publisher" class="ig"><span class="k">출판사</span><span class="v">{{ manga.publisher }}</span></div>
            <div class="ig"><span class="k">상태</span><span class="v">{{ manga.status === 'COMPLETED' ? '완결' : '연재중' }}</span></div>
          </div>
        </div>

        <!-- 감상평 -->
        <div class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>감상평</h2><span class="count">{{ comments.length }}개</span></div>
          <div class="cmt">
            <div class="cin">
              <div class="av"></div>
              <input v-model="newComment" placeholder="이 만화에 대한 감상을 남겨보세요" @keyup.enter="submitComment" />
              <button @click="submitComment">등록</button>
            </div>
            <div v-for="c in comments" :key="c.id" class="citem">
              <div class="cav"></div>
              <div class="cbody">
                <div class="cmeta">
                  <span class="cu">{{ c.user?.nickname || c.user?.username || '익명' }}</span>
                  <span class="ct">{{ (c.created_at || '').slice(0, 10) }}</span>
                  <span v-if="c.user?.id === myUserId && editingId !== c.id" style="margin-left:auto;display:flex;gap:14px;color:var(--muted);font-size:13px;font-weight:500;cursor:pointer">
                    <span @click="startEdit(c)">수정</span>
                    <span @click="removeComment(c)">삭제</span>
                  </span>
                </div>
                <template v-if="editingId === c.id">
                  <div class="cin" style="margin:6px 0 0">
                    <input v-model="editText" @keyup.enter="saveEdit(c)" />
                    <button @click="saveEdit(c)">저장</button>
                  </div>
                  <div style="margin-top:6px"><span style="cursor:pointer;color:var(--muted-2);font-size:12px" @click="cancelEdit">취소</span></div>
                </template>
                <p v-else>{{ c.is_deleted ? '삭제된 댓글입니다.' : c.content }}</p>
              </div>
            </div>
            <div v-if="!comments.length" class="note">아직 감상평이 없어요. 첫 감상을 남겨보세요!</div>
          </div>
        </div>
      </div>

      <!-- 애니 ↔ 만화 매핑 모달 -->
      <div v-if="showAnimeModal" class="modal-overlay" @click.self="showAnimeModal = false">
        <div class="modal-panel">
          <button class="modal-close" @click="showAnimeModal = false" aria-label="닫기">✕</button>
          <div class="modal-head">
            <div class="lab">▸ 애니 ↔ 원작 만화</div>
            <h3>{{ manga.title }} · 시즌별 이어보기</h3>
          </div>
          <div class="modal-list">
            <div v-for="m in sortedMappings" :key="m.id" class="modal-map">
              <div class="linkcover">
                <div class="lc cv-anime" :style="{ background: animeGradient(m.anime?.title || '') }"><span class="lct">{{ m.anime?.title }}</span></div>
                <div class="ld"><div class="ln">{{ m.anime?.title }}</div><div class="lm">{{ m.anime?.release_year }}</div></div>
              </div>
              <div class="coordbox">
                <div class="ic"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></div>
                <div class="ctxt"><div class="cl">애니가 다루는 범위</div><div class="cv"><b>{{ rangeText(m) }}</b></div></div>
              </div>
              <button v-if="m.anime" class="go" @click="goAnime(m.anime.id)">
                애니 정보 보기
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.info-banner {
  display: flex;
  gap: 14px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 18px;
  padding: 14px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
  box-shadow: 0 18px 36px -26px rgba(60, 40, 90, 0.35);
}
.info-banner:hover {
  transform: translateY(-2px);
  border-color: var(--glow);
  box-shadow: 0 22px 40px -22px rgba(124, 77, 239, 0.4);
}
.ab-cover {
  width: 58px;
  aspect-ratio: 3 / 4;
  border-radius: 10px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  color: #fff;
}
.ab-cover-t {
  font-family: 'Black Han Sans', sans-serif;
  font-size: 13px;
  z-index: 2;
}
.ab-body {
  min-width: 0;
}
.ab-lab {
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--spot-deep);
  font-weight: 700;
}
.ab-title {
  font-family: 'Black Han Sans', sans-serif;
  font-size: 16px;
  margin: 3px 0 6px;
  line-height: 1.2;
}
.ab-cta {
  font-size: 12.5px;
  color: var(--glow);
  font-weight: 600;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(26, 22, 34, 0.55);
  backdrop-filter: blur(3px);
  display: grid;
  place-items: center;
  padding: 20px;
  animation: fade 0.2s ease;
}
.modal-panel {
  position: relative;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  overflow-y: auto;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 22px;
  padding: 24px;
  box-shadow: 0 40px 80px -30px rgba(20, 10, 40, 0.6);
}
.modal-close {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--line-2);
  background: var(--surface-2);
  color: var(--ink-soft);
  font-size: 14px;
  cursor: pointer;
}
.modal-close:hover {
  border-color: var(--spot);
  color: var(--spot-deep);
}
.modal-head {
  margin-bottom: 18px;
  padding-right: 36px;
}
.modal-head .lab {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--spot-deep);
  font-weight: 700;
}
.modal-head h3 {
  font-family: 'Black Han Sans', sans-serif;
  font-weight: 400;
  font-size: 22px;
  margin-top: 5px;
  line-height: 1.2;
}
.modal-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modal-map {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  background: var(--surface-2);
}
.modal-map .linkcover {
  align-items: center;
  gap: 12px;
}
.modal-map .lc {
  width: 56px;
}
.modal-map .ld .ln {
  font-size: 14.5px;
  line-height: 1.25;
}
.modal-map .coordbox {
  margin-top: 12px;
}
/* 모달 안 .go 버튼은 base의 .bridge-box .go 범위 밖이라 직접 스타일 지정 */
.modal-map .go {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  margin-top: 12px;
  background: linear-gradient(100deg, var(--glow), var(--spot));
  color: #fff;
  border: none;
  font-family: inherit;
  font-weight: 700;
  font-size: 14px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 10px 22px -8px rgba(124, 77, 239, 0.45);
}
.modal-map .go:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px -8px rgba(255, 62, 100, 0.5);
}
</style>

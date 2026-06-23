<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAnime, getAnimeMangaMappings, getAnimeComments, postAnimeComment, deleteAnimeComment, patchAnimeComment, addFavorite, removeFavorite, getMyFavorites, getSession } from '../api'
import { animeGradient, realImage, ratingText } from '../utils/cover'
import { ytSearch } from '../utils/youtube'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()

const loading = ref(true)
const notFound = ref(false)
const anime = ref(null)
const mappings = ref([])
const comments = ref([])
const newComment = ref('')
const favId = ref(null)
const posting = ref(false)
const myUserId = ref(null)
const editingId = ref(null)
const editText = ref('')

async function refreshComments() {
  const r = await getAnimeComments(anime.value.id)
  comments.value = r.results || []
}
async function removeComment(c) {
  if (!confirm('이 댓글을 삭제할까요?')) return
  try {
    await deleteAnimeComment(anime.value.id, c.id)
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
    await patchAnimeComment(anime.value.id, c.id, content)
    cancelEdit()
    await refreshComments()
  } catch (e) {
    alert('수정에 실패했어요.')
  }
}

const gradient = computed(() => (anime.value ? animeGradient(anime.value.title) : ''))
const poster = computed(() => realImage(anime.value?.poster_image_url))
const primaryMapping = computed(() => mappings.value[0] || null)
const hasContinuePoint = computed(() => {
  const m = primaryMapping.value
  return !!(m && (m.continue_chapter || m.continue_volume))
})
const continueText = computed(() => {
  const m = primaryMapping.value
  if (!m) return ''
  if (m.continue_volume && m.continue_chapter) return `${m.continue_volume}권 ${m.continue_chapter}화`
  if (m.continue_chapter) return `${m.continue_chapter}화`
  return m.mapping_text
})

async function toggleFavorite() {
  if (!anime.value) return
  try {
    if (favId.value) {
      await removeFavorite(favId.value)
      favId.value = null
    } else {
      const fav = await addFavorite('ANIME', anime.value.id)
      favId.value = fav.id
    }
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      if (confirm('찜하려면 로그인이 필요해요. 로그인 페이지로 이동할까요?')) router.push('/login')
    } else {
      alert('처리 중 오류가 발생했어요.')
    }
  }
}

async function submitComment() {
  const content = newComment.value.trim()
  if (!content || posting.value) return
  posting.value = true
  try {
    await postAnimeComment(anime.value.id, content)
    newComment.value = ''
    const c = await getAnimeComments(anime.value.id)
    comments.value = c.results || []
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      if (confirm('댓글을 남기려면 로그인이 필요해요. 로그인할까요?')) router.push('/login')
    } else {
      alert('댓글 등록에 실패했어요.')
    }
  } finally {
    posting.value = false
  }
}

onMounted(async () => {
  try {
    anime.value = await getAnime(props.id)
    const [mp, cm] = await Promise.allSettled([
      getAnimeMangaMappings(props.id),
      getAnimeComments(props.id),
    ])
    if (mp.status === 'fulfilled') mappings.value = mp.value.mappings || []
    if (cm.status === 'fulfilled') comments.value = cm.value.results || []
    // 이미 찜한 작품이면 버튼 상태 반영 (로그인 안 했으면 조용히 무시)
    try {
      const s = await getSession()
      if (s.authenticated) {
        myUserId.value = s.user?.id
        const favs = await getMyFavorites()
        const f = (favs.results || []).find((x) => x.target_type === 'ANIME' && x.target_id === anime.value.id)
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
    <div v-else-if="notFound" class="state-msg"><div class="big">작품을 찾을 수 없어요</div><RouterLink to="/anime" style="color:var(--spot-deep)">애니 목록으로</RouterLink></div>

    <template v-else>
      <div class="crumb">
        <RouterLink to="/">홈</RouterLink><span class="sep">/</span>
        <RouterLink to="/anime">애니</RouterLink><span class="sep">/</span>
        <span class="cur">{{ anime.title }}</span>
      </div>

      <div class="dhero anime">
        <div class="banner"><div class="bg" :style="{ background: gradient }"></div><div class="scrim"></div></div>
        <div class="body">
          <div class="poster cv-anime" :style="{ background: gradient }">
            <img v-if="poster" class="real" :src="poster" :alt="anime.title" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:1" />
            <span class="ribbon">{{ anime.type || 'ANIME' }}</span>
            <span class="pt">{{ anime.title }}</span>
          </div>
          <div class="headinfo">
            <span class="kind anime">● 애니메이션</span>
            <h1>{{ anime.title }}</h1>
            <div v-if="anime.original_title" class="orig">{{ anime.original_title }}</div>
            <div class="metarow">
              <span v-if="anime.type" class="chip">유형 <b>{{ anime.type }}</b></span>
              <span v-if="anime.release_year" class="chip">방영 <b>{{ anime.release_year }}</b></span>
              <span v-if="anime.episode_count" class="chip">화수 <b>{{ anime.episode_count }}화</b></span>
              <span v-if="anime.studio" class="chip">제작 <b>{{ anime.studio }}</b></span>
              <span v-if="anime.status === 'COMPLETED'" class="chip status-done">완결</span>
            </div>
            <div class="statline">
              <div class="rate"><span class="star">★</span><span class="num">{{ ratingText(anime.rating_avg) }}</span><span class="cnt">{{ anime.rating_count }}명 평가</span></div>
              <div class="actions">
                <button class="btn" :class="{ active: favId }" :aria-label="favId ? '찜 취소' : '찜하기'" @click="toggleFavorite">{{ favId ? '♥' : '♡' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-body">
        <div v-if="anime.synopsis" class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>줄거리</h2></div>
          <p class="prose">{{ anime.synopsis }}</p>
          <div v-if="anime.tags && anime.tags.length" class="tags">
            <span v-for="t in anime.tags" :key="t.id" class="tag"><span class="h">#</span>{{ t.name }}</span>
          </div>
        </div>

        <!-- ★ 애니-만화 매핑 (핵심) -->
        <div v-if="primaryMapping" class="map-strip">
          <div class="ms-cover cv-manga"><span class="mband" style="background:#7C4DEF">{{ primaryMapping.manga?.title }}</span></div>
          <div class="ms-main">
            <div class="ms-label">📚 애니를 다 봤다면, <b>원작 만화는</b></div>
            <div v-if="hasContinuePoint" class="ms-coord">{{ continueText }}<small>부터 이어 보세요</small></div>
            <div v-else class="ms-coord">{{ primaryMapping.manga?.title }}<small>원작 만화 · 이어보기 지점 준비중</small></div>
          </div>
          <button class="ms-cta" v-if="primaryMapping.manga" @click="router.push({ name: 'manga-detail', params: { id: primaryMapping.manga.id } })">
            원작 만화 보기
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </button>
        </div>

        <!-- 공식 영상 (YouTube 검색 외부 연결) -->
        <div class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>공식 영상</h2><span class="count">YouTube로 연결</span></div>
          <div class="vbar">
            <a class="vbtn" :href="ytSearch(anime.title, 'PV')" target="_blank" rel="noopener"><span>트레일러</span><svg class="ext" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M7 17L17 7M9 7h8v8"/></svg></a>
            <a class="vbtn" :href="ytSearch(anime.title, 'OP')" target="_blank" rel="noopener"><span>오프닝</span><svg class="ext" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M7 17L17 7M9 7h8v8"/></svg></a>
            <a class="vbtn" :href="ytSearch(anime.title, 'ED')" target="_blank" rel="noopener"><span>엔딩</span><svg class="ext" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M7 17L17 7M9 7h8v8"/></svg></a>
          </div>
          <div class="note">각 버튼을 누르면 유튜브 검색 결과가 새 탭에서 열립니다. (공식 영상 API는 추후 연동)</div>
        </div>

        <!-- 작품 정보 -->
        <div class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>작품 정보</h2></div>
          <div class="infogrid">
            <div v-if="anime.original_title" class="ig"><span class="k">원제</span><span class="v">{{ anime.original_title }}</span></div>
            <div v-if="anime.studio" class="ig"><span class="k">제작사</span><span class="v">{{ anime.studio }}</span></div>
            <div v-if="anime.release_year" class="ig"><span class="k">방영</span><span class="v">{{ anime.release_year }}</span></div>
            <div v-if="anime.episode_count" class="ig"><span class="k">화수</span><span class="v">전 {{ anime.episode_count }}화</span></div>
            <div class="ig"><span class="k">유형</span><span class="v">{{ anime.type || '-' }}</span></div>
            <div class="ig"><span class="k">상태</span><span class="v">{{ anime.status === 'COMPLETED' ? '완결' : anime.status === 'UPCOMING' ? '방영예정' : '방영중' }}</span></div>
          </div>
        </div>

        <!-- 감상평 -->
        <div class="section">
          <div class="sec-head"><span class="bar-i"></span><h2>감상평</h2><span class="count">{{ comments.length }}개</span></div>
          <div class="cmt">
            <div class="cin">
              <div class="av"></div>
              <input v-model="newComment" placeholder="이 애니에 대한 감상을 남겨보세요" @keyup.enter="submitComment" />
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
    </template>
  </div>
</template>

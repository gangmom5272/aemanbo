<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getManga, getMangaEpisodes, getMangaAnimeMappings, getMangaComments, postMangaComment, addFavorite, removeFavorite } from '../api'
import { mangaColor, realImage, ratingText } from '../utils/cover'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()

const loading = ref(true)
const notFound = ref(false)
const manga = ref(null)
const episodes = ref([])
const mappings = ref([])
const comments = ref([])
const newComment = ref('')
const favId = ref(null)
const posting = ref(false)

const band = computed(() => (manga.value ? mangaColor(manga.value.title) : '#7C4DEF'))
const cover = computed(() => realImage(manga.value?.cover_image_url))
const primaryMapping = computed(() => mappings.value[0] || null)
const continueChapter = computed(() => {
  const m = primaryMapping.value
  if (!m) return null
  return m.continue_chapter || null
})

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
    const [ep, mp, cm] = await Promise.allSettled([
      getMangaEpisodes(props.id),
      getMangaAnimeMappings(props.id),
      getMangaComments(props.id),
    ])
    if (ep.status === 'fulfilled') episodes.value = ep.value.results || []
    if (mp.status === 'fulfilled') mappings.value = mp.value.mappings || []
    if (cm.status === 'fulfilled') comments.value = cm.value.results || []
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
                <button class="btn" :class="{ active: favId }" @click="toggleFavorite">{{ favId ? '♥ 관심작품' : '♡ 관심작품' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="cols">
        <div class="main">
          <div v-if="manga.description" class="section">
            <div class="sec-head"><span class="bar-i"></span><h2>작품 소개</h2></div>
            <p class="prose">{{ manga.description }}</p>
            <div v-if="manga.tags && manga.tags.length" class="tags">
              <span v-for="t in manga.tags" :key="t.id" class="tag"><span class="h">#</span>{{ t.name }}</span>
            </div>
          </div>

          <div class="section">
            <div class="sec-head"><span class="bar-i"></span><h2>단행본</h2><span class="count">{{ episodes.length }}화</span></div>
            <div v-if="episodes.length" class="vol">
              <div
                v-for="ep in episodes"
                :key="ep.id"
                class="vrow"
                :class="{ continue: continueChapter && ep.chapter_number === continueChapter }"
              >
                <div class="vn">{{ ep.volume_number || '-' }}</div>
                <div class="vmeta">
                  <div class="vt">{{ ep.volume_number ? ep.volume_number + '권' : '' }}<template v-if="ep.title"> · {{ ep.title }}</template></div>
                  <div class="vs">{{ ep.chapter_number ? ep.chapter_number + '화' : '' }}<template v-if="ep.published_at"> · {{ ep.published_at }}</template></div>
                </div>
                <span v-if="continueChapter && ep.chapter_number === continueChapter" class="cflag">여기부터 ▸</span>
                <div class="vr"><span class="star">★</span> {{ ratingText(ep.rating_avg) }}</div>
              </div>
            </div>
            <div v-else class="note">단행본 정보가 아직 없어요.</div>
          </div>

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
                  <div class="cmeta"><span class="cu">{{ c.user?.username || '익명' }}</span><span class="ct">{{ (c.created_at || '').slice(0, 10) }}</span></div>
                  <p>{{ c.is_deleted ? '삭제된 댓글입니다.' : c.content }}</p>
                </div>
              </div>
              <div v-if="!comments.length" class="note">아직 감상평이 없어요. 첫 감상을 남겨보세요!</div>
            </div>
          </div>
        </div>

        <aside class="aside">
          <div v-if="primaryMapping && primaryMapping.anime" class="bridge-box">
            <div class="top"><div class="lab">▸ 영상으로 만나기</div><div class="ttl">이 작품의<br />애니메이션</div></div>
            <div class="mid">
              <div class="linkcover">
                <div class="lc cv-anime" :style="{ background: 'linear-gradient(150deg,#5B2BD6,#9D3CE0 55%,#2D6BD4)' }"><span class="lct">{{ primaryMapping.anime.title }}</span></div>
                <div class="ld"><div class="ln">{{ primaryMapping.anime.title }}</div><div class="lm">{{ primaryMapping.anime.release_year }}</div></div>
              </div>
              <div class="coordbox">
                <div class="ic"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></div>
                <div class="ctxt"><div class="cl">애니가 다루는 범위</div><div class="cv"><b>{{ rangeText(primaryMapping) }}</b></div></div>
              </div>
              <button class="go" @click="router.push({ name: 'anime-detail', params: { id: primaryMapping.anime.id } })">
                애니 정보 보기
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </button>
            </div>
          </div>

          <div class="minicard">
            <h3>작품 정보</h3>
            <div class="infolist">
              <div v-if="manga.original_title" class="ir"><span class="k">원제</span><span class="v">{{ manga.original_title }}</span></div>
              <div v-if="manga.author" class="ir"><span class="k">작가</span><span class="v">{{ manga.author }}</span></div>
              <div v-if="manga.publisher" class="ir"><span class="k">출판사</span><span class="v">{{ manga.publisher }}</span></div>
              <div class="ir"><span class="k">상태</span><span class="v">{{ manga.status === 'COMPLETED' ? '완결' : '연재중' }}</span></div>
            </div>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSession, getMyFavorites, getMyComments, logout } from '../api'
import { animeGradient, mangaColor, statusBadge, animeStatusBadge } from '../utils/cover'

const router = useRouter()
const loading = ref(true)
const authed = ref(false)
const user = ref(null)
const favorites = ref([])
const comments = ref([])

const initial = computed(() => (user.value?.nickname || user.value?.username || '?').slice(0, 1))

function coverStyle(f) {
  if (f.target_type === 'ANIME') return { background: animeGradient(f.target?.title || '') }
  return { background: mangaColor(f.target?.title || '') }
}
function badge(f) {
  return f.target_type === 'ANIME' ? animeStatusBadge(f.target?.status) : statusBadge(f.target?.status)
}
function openFav(f) {
  if (!f.target) return
  router.push({ name: f.target_type === 'ANIME' ? 'anime-detail' : 'manga-detail', params: { id: f.target.id } })
}
function openComment(c) {
  router.push({ name: c.target_type === 'ANIME' ? 'anime-detail' : 'manga-detail', params: { id: c.target_id } })
}
async function doLogout() {
  try { await logout() } catch (_) {}
  router.push('/')
}

onMounted(async () => {
  try {
    const s = await getSession()
    authed.value = !!s.authenticated
    user.value = s.user
    if (authed.value) {
      const [f, c] = await Promise.allSettled([getMyFavorites(), getMyComments()])
      if (f.status === 'fulfilled') favorites.value = f.value.results || []
      if (c.status === 'fulfilled') comments.value = c.value.results || []
    }
  } catch (e) {
    authed.value = false
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="wrap">
    <div v-if="loading" class="state-msg">불러오는 중…</div>

    <div v-else-if="!authed" class="state-msg">
      <div class="big">로그인이 필요해요</div>
      마이페이지는 로그인 후 이용할 수 있어요.
      <div style="margin-top:18px"><button class="pbtn primary" @click="router.push('/login')">로그인하러 가기</button></div>
    </div>

    <template v-else>
      <div class="profile">
        <div class="avatar">{{ initial }}</div>
        <div class="p-info">
          <div class="pname">{{ user.nickname || user.username }}</div>
          <div class="pmeta">@{{ user.username }}<template v-if="user.joined_at"> · 가입 {{ (user.joined_at || '').slice(0, 10) }}</template></div>
          <div class="pbtns">
            <button class="pbtn primary">프로필 편집</button>
            <button class="pbtn" @click="doLogout">로그아웃</button>
          </div>
        </div>
        <div class="p-stats">
          <div class="stat"><div class="n">{{ favorites.length }}</div><div class="l">찜한 작품</div></div>
          <div class="stat"><div class="n">{{ comments.length }}</div><div class="l">활동 수</div></div>
        </div>
      </div>

      <div class="msec">
        <div class="msec-head"><span class="ico">♥</span><h2>찜한 콘텐츠</h2></div>
        <div v-if="favorites.length" class="fav-grid">
          <article v-for="f in favorites" :key="f.id" class="fcard" @click="openFav(f)">
            <div class="art" :class="f.target_type === 'ANIME' ? 'cv-anime' : 'cv-manga'" :style="coverStyle(f)">
              <span class="kindtag" :class="f.target_type === 'ANIME' ? 'anime' : 'manga'">{{ f.target_type }}</span>
              <span class="fbadge" :class="badge(f).cls">{{ badge(f).label }}</span>
              <span class="ft">{{ f.target?.title || '(삭제됨)' }}</span>
            </div>
            <div class="finfo"><div class="fn">{{ f.target?.title || '-' }}</div><div class="fs">{{ f.status_label || (f.target_type === 'ANIME' ? '애니메이션' : '만화') }}</div></div>
          </article>
        </div>
        <div v-else class="note">아직 찜한 작품이 없어요.</div>
      </div>

      <div class="msec">
        <div class="msec-head"><span class="ico">↺</span><h2>나의 활동</h2></div>
        <div v-if="comments.length" class="act-list">
          <div v-for="c in comments" :key="c.target_type + '-' + c.id" class="arow" @click="openComment(c)">
            <div class="athumb" :class="c.target_type === 'ANIME' ? 'cv-anime' : 'cv-manga'" :style="c.target_type === 'ANIME' ? { background: animeGradient(c.target_title) } : { background: mangaColor(c.target_title) }">
              <span class="ai">{{ (c.target_title || '?').slice(0, 1) }}</span>
            </div>
            <div class="abody">
              <div class="akind">댓글</div>
              <div class="atitle">{{ c.target_title }}</div>
              <div class="atext review">"{{ c.content }}"</div>
            </div>
            <div class="atime">{{ (c.created_at || '').slice(0, 10) }}</div>
          </div>
        </div>
        <div v-else class="note">아직 활동 내역이 없어요.</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSession, getMyFavorites, getMyComments, logout, updateMyProfile, uploadAvatar } from '../api'
import { animeGradient, mangaColor, statusBadge, animeStatusBadge } from '../utils/cover'

const router = useRouter()
const loading = ref(true)
const authed = ref(false)
const user = ref(null)
const favorites = ref([])
const comments = ref([])

const initial = computed(() => (user.value?.nickname || user.value?.username || '?').slice(0, 1))
const avatarUrl = computed(() => user.value?.profile_image_url || '')

// 프로필 편집
const showEdit = ref(false)
const editNickname = ref('')
const avatarFile = ref(null)
const avatarPreview = ref('')
const saving = ref(false)
const editError = ref('')

function openEdit() {
  editNickname.value = user.value?.nickname || ''
  avatarFile.value = null
  avatarPreview.value = ''
  editError.value = ''
  showEdit.value = true
}
function onPickFile(e) {
  const f = e.target.files && e.target.files[0]
  if (!f) return
  avatarFile.value = f
  avatarPreview.value = URL.createObjectURL(f)
}
async function saveProfile() {
  if (saving.value) return
  saving.value = true
  editError.value = ''
  try {
    if (avatarFile.value) {
      const r = await uploadAvatar(avatarFile.value)
      if (user.value) user.value.profile_image_url = r.profile_image_url
    }
    const nick = editNickname.value.trim()
    if (nick && nick !== user.value?.nickname) {
      const u = await updateMyProfile({ nickname: nick })
      if (user.value) user.value.nickname = u.nickname
    }
    showEdit.value = false
  } catch (e) {
    if (e.status === 401 || e.status === 403) editError.value = '권한이 없어요. 다시 로그인해 주세요.'
    else if (e.status === 400) editError.value = (e.data && e.data.nickname && e.data.nickname[0]) || '이미 사용 중인 닉네임이거나 입력이 올바르지 않아요.'
    else editError.value = '저장 중 오류가 발생했어요.'
  } finally {
    saving.value = false
  }
}

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
        <div class="avatar">
          <img v-if="avatarUrl" :src="avatarUrl" alt="" class="avatar-img" />
          <template v-else>{{ initial }}</template>
        </div>
        <div class="p-info">
          <div class="pname">{{ user.nickname || user.username }}</div>
          <div class="pmeta">@{{ user.username }}<template v-if="user.joined_at"> · 가입 {{ (user.joined_at || '').slice(0, 10) }}</template></div>
          <div class="pbtns">
            <button class="pbtn primary" @click="openEdit">프로필 편집</button>
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

      <!-- 프로필 편집 모달 -->
      <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
        <div class="modal-panel">
          <button class="modal-close" @click="showEdit = false" aria-label="닫기">✕</button>
          <div class="modal-head"><h3>프로필 편집</h3></div>
          <div class="edit-avatar">
            <div class="avatar">
              <img v-if="avatarPreview || avatarUrl" :src="avatarPreview || avatarUrl" alt="" class="avatar-img" />
              <template v-else>{{ initial }}</template>
            </div>
            <label class="pbtn">사진 변경<input type="file" accept="image/*" hidden @change="onPickFile" /></label>
          </div>
          <label class="edit-field">
            <span>닉네임</span>
            <input v-model="editNickname" maxlength="50" placeholder="닉네임" @keyup.enter="saveProfile" />
          </label>
          <div v-if="editError" class="edit-err">{{ editError }}</div>
          <div class="edit-actions">
            <button class="pbtn" @click="showEdit = false">취소</button>
            <button class="pbtn primary" :disabled="saving" @click="saveProfile">{{ saving ? '저장 중…' : '저장' }}</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.avatar-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  z-index: 1;
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
}
.modal-panel {
  position: relative;
  width: 100%;
  max-width: 420px;
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
  cursor: pointer;
}
.modal-head h3 {
  font-family: 'Black Han Sans', sans-serif;
  font-weight: 400;
  font-size: 22px;
  margin-bottom: 18px;
}
.edit-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.edit-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.edit-field span {
  font-size: 13px;
  color: var(--muted);
  font-weight: 600;
}
.edit-field input {
  height: 44px;
  border: 1px solid var(--line-2);
  border-radius: 11px;
  padding: 0 14px;
  font-family: inherit;
  font-size: 15px;
  background: var(--surface-2);
  outline: none;
}
.edit-field input:focus {
  border-color: var(--glow);
}
.edit-err {
  color: var(--spot-deep);
  font-size: 13px;
  margin-top: 10px;
}
.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
</style>

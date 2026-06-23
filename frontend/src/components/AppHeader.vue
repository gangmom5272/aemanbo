<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSession, logout } from '../api'

const router = useRouter()
const route = useRoute()
const keyword = ref('')
const authed = ref(false)
const showMenu = ref(false)

function submitSearch() {
  const q = keyword.value.trim()
  if (!q) return
  router.push({ name: 'search', query: { keyword: q } })
}

async function checkAuth() {
  try {
    const s = await getSession()
    authed.value = !!s.authenticated
  } catch (e) {
    authed.value = false
  }
}

function toggleMenu() {
  showMenu.value = !showMenu.value
}
function closeMenu() {
  showMenu.value = false
}
function goMypage() {
  closeMenu()
  router.push('/mypage')
}
async function onLogout() {
  closeMenu()
  try {
    await logout()
  } catch (e) {
    /* noop */
  }
  authed.value = false
  router.push('/')
}

onMounted(() => {
  checkAuth()
  document.addEventListener('click', closeMenu)
})
onUnmounted(() => document.removeEventListener('click', closeMenu))
watch(() => route.fullPath, () => {
  checkAuth()
  closeMenu()
})
</script>

<template>
  <header>
    <div class="bar">
      <div class="logo" @click="router.push('/')">
        <span class="glyph"></span>
        <span>
          <span class="word">애<b>만</b>보</span>
          <div class="tag">애니 보고 · 만화 보고</div>
        </span>
      </div>
      <label class="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
        <input v-model="keyword" placeholder="애니나 만화 제목을 검색하세요" @keyup.enter="submitSearch" />
      </label>
      <nav class="nav">
        <RouterLink to="/">홈</RouterLink>
        <RouterLink to="/anime">애니</RouterLink>
        <RouterLink to="/manga">만화</RouterLink>
        <div v-if="authed" class="user-menu" @click.stop>
          <div class="uic" title="내 메뉴" @click="toggleMenu"></div>
          <div v-if="showMenu" class="menu">
            <a @click="goMypage">마이페이지</a>
            <a @click="onLogout">로그아웃</a>
          </div>
        </div>
        <RouterLink v-else to="/login">로그인</RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.user-menu {
  position: relative;
}
.user-menu .uic {
  cursor: pointer;
}
.menu {
  position: absolute;
  right: 0;
  top: 46px;
  min-width: 150px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 12px;
  box-shadow: 0 18px 40px -18px rgba(40, 30, 60, 0.45);
  padding: 6px;
  display: flex;
  flex-direction: column;
  z-index: 80;
}
.menu a {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-soft);
  cursor: pointer;
}
.menu a:hover {
  background: var(--surface-2);
  color: var(--ink);
}
</style>

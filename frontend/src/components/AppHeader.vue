<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const keyword = ref('')

function submitSearch() {
  const q = keyword.value.trim()
  if (!q) return
  router.push({ name: 'search', query: { keyword: q } })
}
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
        <RouterLink to="/mypage">마이페이지</RouterLink>
        <div class="uic" title="마이페이지" @click="router.push('/mypage')"></div>
      </nav>
    </div>
  </header>
</template>

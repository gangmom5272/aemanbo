<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import ChatFab from './components/ChatFab.vue'
import { getCsrf } from './api'

const route = useRoute()
// 로그인/콜백 같은 'bare' 화면에서는 헤더/푸터/FAB 숨김
const bare = computed(() => route.meta.bare === true)

// CSRF 쿠키 확보 (찜·댓글·프로필 수정 등 POST/PATCH 동작용)
onMounted(() => {
  getCsrf().catch(() => {})
})
</script>

<template>
  <div class="app-shell">
    <AppHeader v-if="!bare" />
    <main class="app-main">
      <RouterView v-slot="{ Component, route: r }">
        <keep-alive :include="['AnimeListView', 'MangaListView']">
          <component :is="Component" :key="r.meta.keep ? r.name : r.fullPath" class="page-fade" />
        </keep-alive>
      </RouterView>
    </main>
    <AppFooter v-if="!bare" />
  </div>
  <ChatFab v-if="!bare" />
</template>

<style>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-main {
  flex: 1 0 auto;
}
.app-shell > footer {
  flex-shrink: 0;
}
</style>

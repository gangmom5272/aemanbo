<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import ChatFab from './components/ChatFab.vue'

const route = useRoute()
// 로그인/콜백 같은 'bare' 화면에서는 헤더/푸터/FAB 숨김
const bare = computed(() => route.meta.bare === true)
</script>

<template>
  <AppHeader v-if="!bare" />
  <RouterView v-slot="{ Component }">
    <component :is="Component" :key="route.fullPath" class="page-fade" />
  </RouterView>
  <AppFooter v-if="!bare" />
  <ChatFab v-if="!bare" />
</template>

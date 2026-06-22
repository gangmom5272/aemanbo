import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { bare: true } },
  { path: '/auth/callback/:provider', name: 'oauth-callback', component: () => import('../views/OAuthCallbackView.vue'), meta: { bare: true } },
  { path: '/anime', name: 'anime-list', component: () => import('../views/AnimeListView.vue') },
  { path: '/manga', name: 'manga-list', component: () => import('../views/MangaListView.vue') },
  { path: '/search', name: 'search', component: () => import('../views/SearchView.vue') },
  { path: '/anime/:id', name: 'anime-detail', component: () => import('../views/AnimeDetailView.vue'), props: true },
  { path: '/manga/:id', name: 'manga-detail', component: () => import('../views/MangaDetailView.vue'), props: true },
  { path: '/mypage', name: 'mypage', component: () => import('../views/MyPageView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router

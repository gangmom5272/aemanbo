<script setup>
import { ref, computed, onMounted } from 'vue'
import { listMangas, getHome } from '../api'
import WorkCard from '../components/WorkCard.vue'

const loading = ref(true)
const usingFallback = ref(false)
const items = ref([])
const sort = ref('name')

const sorts = [
  { key: 'name', label: '가나다순' },
  { key: 'pop', label: '인기순' },
  { key: 'recent', label: '최신순' },
  { key: 'rating', label: '평점순' },
]

const sorted = computed(() => {
  const arr = items.value.slice()
  if (sort.value === 'name') arr.sort((a, b) => (a.title || '').localeCompare(b.title || '', 'ko'))
  else if (sort.value === 'pop') arr.sort((a, b) => (b.favorite_count || 0) - (a.favorite_count || 0))
  else if (sort.value === 'rating') arr.sort((a, b) => (b.rating_avg || 0) - (a.rating_avg || 0))
  return arr
})

onMounted(async () => {
  try {
    // TODO(백엔드): GET /api/v1/mangas/ 미구현
    const data = await listMangas()
    items.value = data.results || data || []
  } catch (e) {
    usingFallback.value = true
    try {
      const home = await getHome()
      items.value = home.popular_mangas || []
    } catch (_) {
      items.value = []
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="wrap">
    <div class="crumb"><RouterLink to="/">홈</RouterLink><span class="sep">/</span><span class="cur">만화</span></div>
    <div class="list-head">
      <div class="lt">만화 <span class="cnt">{{ sorted.length }}작품</span></div>
      <div class="sortbar">
        <button v-for="s in sorts" :key="s.key" :class="{ on: sort === s.key }" @click="sort = s.key">{{ s.label }}</button>
      </div>
    </div>

    <div v-if="usingFallback" class="todo-banner">
      <span class="b">TODO</span>
      전체 만화 목록 API(<code>GET /api/v1/mangas/</code>)는 아직 백엔드 미구현이라 임시로 인기 만화를 보여주고 있어요.
    </div>

    <div v-if="loading" class="state-msg">불러오는 중…</div>
    <div v-else-if="!sorted.length" class="state-msg"><div class="big">작품이 없습니다</div>시드 데이터를 넣거나 목록 API를 구현해 주세요.</div>
    <div v-else class="grid">
      <WorkCard v-for="m in sorted" :key="m.id" :work="m" kind="manga" variant="grid" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listAnimes } from '../api'
import WorkCard from '../components/WorkCard.vue'

const loading = ref(true)
const loadingMore = ref(false)
const error = ref(false)
const items = ref([])
const sort = ref('name')
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)

const sorts = [
  { key: 'name', label: '가나다순' },
  { key: 'recent', label: '최신순' },
  { key: 'rating', label: '평점순' },
]

async function load(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
  }
  const first = page.value === 1
  if (first) loading.value = true
  else loadingMore.value = true
  error.value = false
  try {
    const data = await listAnimes({ sort: sort.value, page: page.value, page_size: 30 })
    const results = data.results || []
    items.value = first ? results : [...items.value, ...results]
    total.value = data.count ?? items.value.length
    totalPages.value = data.total_pages ?? 1
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function changeSort(key) {
  if (sort.value === key) return
  sort.value = key
  load(true)
}
function loadMore() {
  if (page.value < totalPages.value) {
    page.value += 1
    load()
  }
}

onMounted(() => load(true))
</script>

<template>
  <div class="wrap">
    <div class="crumb"><RouterLink to="/">홈</RouterLink><span class="sep">/</span><span class="cur">애니메이션</span></div>
    <div class="list-head">
      <div class="lt">애니메이션 <span class="cnt">{{ total }}작품</span></div>
      <div class="sortbar">
        <button v-for="s in sorts" :key="s.key" :class="{ on: sort === s.key }" @click="changeSort(s.key)">{{ s.label }}</button>
      </div>
    </div>

    <div v-if="loading" class="state-msg">불러오는 중…</div>
    <div v-else-if="error" class="state-msg"><div class="big">목록을 불러오지 못했어요</div>Django 서버(8000)가 켜져 있는지 확인하세요.</div>
    <div v-else-if="!items.length" class="state-msg"><div class="big">작품이 없습니다</div>데이터를 적재해 주세요.</div>
    <template v-else>
      <div class="grid">
        <WorkCard v-for="a in items" :key="a.id" :work="a" kind="anime" variant="grid" />
      </div>
      <div v-if="page < totalPages" style="text-align:center;padding:6px 0 50px">
        <button class="btn" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? '불러오는 중…' : '더 보기' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getHome } from '../api'
import WorkCard from '../components/WorkCard.vue'

const router = useRouter()
const keyword = ref('')
const loading = ref(true)
const error = ref(false)
const animes = ref([])
const mangas = ref([])
const mappings = ref([])
const mappingCards = computed(() => mappings.value.filter((m) => m.anime))

const quicks = ['주술회전', '진격의 거인', '체인소 맨', '귀멸의 칼날', '스파이 패밀리']

function doSearch(q) {
  const term = (q ?? keyword.value).trim()
  if (!term) return
  router.push({ name: 'search', query: { keyword: term } })
}

onMounted(async () => {
  try {
    const data = await getHome()
    animes.value = data.popular_animes || []
    mangas.value = data.popular_mangas || []
    mappings.value = data.recommended_mappings || []
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <div class="aura"></div>
    <div class="wrap">
      <section class="search-hero">
        <div class="eyebrow"><span class="dot"></span>애니 보고 · 만화 보고</div>
        <h1>무엇을 찾고<br />계신가요?</h1>
        <p class="sub">제목을 검색하면 <b style="color:var(--ink-soft)">애니 ↔ 원작 만화 이어보기 정보</b>까지 한 번에.</p>
        <div class="bigsearch">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input v-model="keyword" placeholder="애니메이션, 만화, 작가 이름으로 검색…" @keyup.enter="doSearch()" />
          <button class="go-s" @click="doSearch()">검색</button>
        </div>
        <div class="quick">
          <span class="ql">인기 검색</span>
          <span v-for="q in quicks" :key="q" class="qchip" @click="doSearch(q)">{{ q }}</span>
        </div>
      </section>

      <div v-if="error" class="todo-banner">
        <span class="b">API</span>
        백엔드(<code>/api/v1/home/</code>)에 연결하지 못했습니다. Django 서버를 8000 포트로 실행했는지 확인하세요.
      </div>

      <!-- 추천 매핑 카드 -->
      <section v-if="mappingCards.length" class="block">
        <div class="head">
          <div class="titles"><span class="kicker">// PICK UP</span><h2>오늘의 이어보기</h2></div>
          <span class="more" @click="router.push('/anime')">전체 애니 ›</span>
        </div>
        <div class="row">
          <WorkCard
            v-for="m in mappingCards"
            :key="m.id"
            :work="m.anime"
            kind="anime"
            variant="row"
            :caption="m.mapping_text"
          />
        </div>
      </section>

      <section class="block">
        <div class="head">
          <div class="titles"><span class="kicker">// THIS SEASON</span><h2>인기 애니</h2></div>
          <span class="more" @click="router.push('/anime')">전체 애니 ›</span>
        </div>
        <div v-if="loading" class="state-msg">불러오는 중…</div>
        <div v-else-if="!animes.length" class="state-msg">표시할 애니가 없습니다. <code>seed_works</code>로 시드 데이터를 넣어보세요.</div>
        <div v-else class="row">
          <WorkCard v-for="(a, i) in animes" :key="a.id" :work="a" kind="anime" variant="row" :rank="i + 1" />
        </div>
      </section>

      <section class="block">
        <div class="head">
          <div class="titles"><span class="kicker">// THIS QUARTER</span><h2>인기 만화</h2></div>
          <span class="more" @click="router.push('/manga')">전체 만화 ›</span>
        </div>
        <div v-if="loading" class="state-msg">불러오는 중…</div>
        <div v-else-if="!mangas.length" class="state-msg">표시할 만화가 없습니다.</div>
        <div v-else class="row">
          <WorkCard v-for="(m, i) in mangas" :key="m.id" :work="m" kind="manga" variant="row" :rank="i + 1" />
        </div>
      </section>
    </div>
  </section>
</template>

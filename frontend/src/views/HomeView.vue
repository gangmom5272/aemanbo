<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getHome, getSession, getGenres, updateMyProfile } from '../api'
import WorkCard from '../components/WorkCard.vue'

const router = useRouter()
const keyword = ref('')
const loading = ref(true)
const error = ref(false)
const animes = ref([])
const mangas = ref([])
const mappings = ref([])
const mappingCards = computed(() => mappings.value.filter((m) => m.anime))

// 첫 로그인 선호 장르 설문
const showSurvey = ref(false)
const genres = ref([])
const selectedGenres = ref([])
const savingSurvey = ref(false)

function doSearch(q) {
  const term = (q ?? keyword.value).trim()
  if (!term) return
  router.push({ name: 'search', query: { keyword: term } })
}

async function loadHome() {
  const data = await getHome()
  animes.value = data.popular_animes || []
  mangas.value = data.popular_mangas || []
  mappings.value = data.recommended_mappings || []
}

function toggleGenre(v) {
  const i = selectedGenres.value.indexOf(v)
  if (i >= 0) selectedGenres.value.splice(i, 1)
  else selectedGenres.value.push(v)
}

async function submitSurvey() {
  if (savingSurvey.value) return
  savingSurvey.value = true
  try {
    await updateMyProfile({ preferred_genres: selectedGenres.value, onboarded: true })
    showSurvey.value = false
    await loadHome() // 선호 장르 반영된 추천으로 새로고침
  } catch (_) {
    showSurvey.value = false
  } finally {
    savingSurvey.value = false
  }
}

async function skipSurvey() {
  if (savingSurvey.value) return
  savingSurvey.value = true
  try {
    await updateMyProfile({ onboarded: true })
  } catch (_) {}
  showSurvey.value = false
  savingSurvey.value = false
}

onMounted(async () => {
  try {
    await loadHome()
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }

  // 로그인했는데 아직 설문 안 한 사용자 → 선호 장르 설문 모달
  try {
    const s = await getSession()
    if (s.authenticated && s.user && !s.user.onboarded) {
      const g = await getGenres()
      genres.value = g.results || []
      selectedGenres.value = [...(s.user.preferred_genres || [])]
      showSurvey.value = true
    }
  } catch (_) {}
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
      </section>

      <div v-if="error" class="todo-banner">
        <span class="b">API</span>
        백엔드(<code>/api/v1/home/</code>)에 연결하지 못했습니다. Django 서버를 8000 포트로 실행했는지 확인하세요.
      </div>

      <!-- 추천 매핑 카드 -->
      <section v-if="mappingCards.length" class="block">
        <div class="head">
          <div class="titles"><h2>🎲 오늘의 랜덤 픽</h2></div>
          <span class="more" @click="router.push('/anime')">전체 애니 ›</span>
        </div>
        <div class="row">
          <WorkCard
            v-for="m in mappingCards"
            :key="m.id"
            :work="m.anime"
            kind="anime"
            variant="row"
          />
        </div>
      </section>

      <section class="block">
        <div class="head">
          <div class="titles"><h2>인기 애니</h2></div>
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
          <div class="titles"><h2>인기 만화</h2></div>
          <span class="more" @click="router.push('/manga')">전체 만화 ›</span>
        </div>
        <div v-if="loading" class="state-msg">불러오는 중…</div>
        <div v-else-if="!mangas.length" class="state-msg">표시할 만화가 없습니다.</div>
        <div v-else class="row">
          <WorkCard v-for="(m, i) in mangas" :key="m.id" :work="m" kind="manga" variant="row" :rank="i + 1" />
        </div>
      </section>
    </div>

    <!-- 첫 로그인 선호 장르 설문 모달 -->
    <div v-if="showSurvey" class="survey-overlay">
      <div class="survey-panel">
        <div class="survey-head">
          <h3>어떤 장르를 좋아하세요?</h3>
          <p>고른 장르를 바탕으로 <b>오늘의 랜덤 픽</b>에서 애니를 추천해 드려요. (여러 개 선택 가능)</p>
        </div>
        <div class="genre-grid">
          <button
            v-for="g in genres"
            :key="g.value"
            class="genre-chip"
            :class="{ on: selectedGenres.includes(g.value) }"
            @click="toggleGenre(g.value)"
          >{{ g.label }}</button>
        </div>
        <div class="survey-actions">
          <button class="pbtn" :disabled="savingSurvey" @click="skipSurvey">건너뛰기</button>
          <button
            class="pbtn primary"
            :disabled="savingSurvey || !selectedGenres.length"
            @click="submitSurvey"
          >{{ savingSurvey ? '저장 중…' : `추천받기 (${selectedGenres.length})` }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.survey-overlay {
  position: fixed;
  inset: 0;
  z-index: 220;
  background: rgba(26, 22, 34, 0.55);
  backdrop-filter: blur(3px);
  display: grid;
  place-items: center;
  padding: 20px;
}
.survey-panel {
  width: 100%;
  max-width: 480px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 22px;
  padding: 26px;
  box-shadow: 0 40px 80px -30px rgba(20, 10, 40, 0.6);
}
.survey-head h3 {
  font-family: 'Black Han Sans', sans-serif;
  font-weight: 400;
  font-size: 23px;
  margin-bottom: 8px;
}
.survey-head p {
  font-size: 13.5px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 20px;
}
.genre-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-bottom: 24px;
}
.genre-chip {
  font-size: 14px;
  padding: 9px 15px;
  border-radius: 30px;
  background: var(--surface-2);
  border: 1px solid var(--line-2);
  color: var(--ink-soft);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.genre-chip:hover {
  border-color: var(--glow);
}
.genre-chip.on {
  background: var(--spot);
  border-color: var(--spot);
  color: #fff;
  font-weight: 600;
}
.survey-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

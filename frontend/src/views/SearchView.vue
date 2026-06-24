<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { search, aiSearch } from '../api'
import WorkCard from '../components/WorkCard.vue'

const route = useRoute()
const loading = ref(false)
const keyword = ref('')
const animes = ref([])
const mangas = ref([])
const aiRecs = ref([])
const aiSource = ref('')
const aiLoading = ref(false)

async function run(q) {
  keyword.value = q
  aiRecs.value = []
  aiSource.value = ''
  if (!q) return
  loading.value = true
  try {
    const data = await search(q)
    animes.value = data.animes || []
    mangas.value = data.mangas || []
  } catch (e) {
    animes.value = []
    mangas.value = []
  } finally {
    loading.value = false
  }
  // 일반 검색 0건일 때만 AI 폴백 호출
  if (!animes.value.length && !mangas.value.length) {
    aiLoading.value = true
    try {
      const data = await aiSearch(q)
      aiRecs.value = data.recommendations || []
      aiSource.value = data.source || ''
    } catch (e) {
      aiRecs.value = []
    } finally {
      aiLoading.value = false
    }
  }
}

onMounted(() => run((route.query.keyword || '').toString()))
watch(() => route.query.keyword, (q) => run((q || '').toString()))
</script>

<template>
  <div class="wrap">
    <div class="crumb"><RouterLink to="/">홈</RouterLink><span class="sep">/</span><span class="cur">검색</span></div>
    <div class="list-head">
      <div class="lt">"{{ keyword }}" <span class="cnt">검색 결과</span></div>
    </div>

    <div v-if="loading" class="state-msg">검색 중…</div>
    <template v-else>
      <section v-if="animes.length" class="block">
        <div class="head"><div class="titles"><h2>애니메이션</h2></div></div>
        <div class="grid"><WorkCard v-for="a in animes" :key="a.id" :work="a" kind="anime" variant="grid" /></div>
      </section>

      <section v-if="mangas.length" class="block">
        <div class="head"><div class="titles"><h2>만화</h2></div></div>
        <div class="grid"><WorkCard v-for="m in mangas" :key="m.id" :work="m" kind="manga" variant="grid" /></div>
      </section>

      <template v-if="!animes.length && !mangas.length && keyword">
        <div v-if="aiLoading" class="state-msg">정확히 일치하는 결과가 없어, AI가 찾고 있어요…</div>
        <section v-else-if="aiRecs.length" class="block">
          <div class="head"><div class="titles"><h2>혹시 이 작품을 찾으세요?</h2></div></div>
          <p class="ai-note">{{ aiSource === 'ai' ? '✦ 제목과 일치하는 결과가 없어, 검색어를 바탕으로 AI가 추천했어요.' : '제목과 일치하진 않지만, 줄거리·장르에서 관련된 작품이에요.' }}</p>
          <div class="grid"><WorkCard v-for="r in aiRecs" :key="r.type + '-' + r.id" :work="r" :kind="r.type" variant="grid" /></div>
        </section>
        <div v-else class="state-msg">
          <div class="big">검색 결과가 없어요</div>다른 키워드로 시도해 보세요.
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.ai-note {
  font-size: 13px;
  color: var(--muted);
  margin: -6px 0 16px;
}
</style>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { search } from '../api'
import WorkCard from '../components/WorkCard.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const keyword = ref('')
const animes = ref([])
const mangas = ref([])
const mappings = ref([])

async function run(q) {
  keyword.value = q
  if (!q) return
  loading.value = true
  try {
    const data = await search(q)
    animes.value = data.animes || []
    mangas.value = data.mangas || []
    mappings.value = data.mappings || []
  } catch (e) {
    animes.value = []; mangas.value = []; mappings.value = []
  } finally {
    loading.value = false
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
      <section v-if="mappings.length" class="block">
        <div class="head"><div class="titles"><span class="kicker">// MAPPING</span><h2>이어보기 매핑</h2></div></div>
        <div class="vol">
          <div v-for="m in mappings" :key="m.id" class="vrow" style="cursor:default">
            <div class="vmeta">
              <div class="vt">{{ m.mapping_text }}</div>
              <div class="vs">{{ m.anime_title }} → {{ m.manga_title }}</div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="animes.length" class="block">
        <div class="head"><div class="titles"><span class="kicker">// ANIME</span><h2>애니메이션</h2></div></div>
        <div class="grid"><WorkCard v-for="a in animes" :key="a.id" :work="a" kind="anime" variant="grid" /></div>
      </section>

      <section v-if="mangas.length" class="block">
        <div class="head"><div class="titles"><span class="kicker">// MANGA</span><h2>만화</h2></div></div>
        <div class="grid"><WorkCard v-for="m in mangas" :key="m.id" :work="m" kind="manga" variant="grid" /></div>
      </section>

      <div v-if="!animes.length && !mangas.length && !mappings.length && keyword" class="state-msg">
        <div class="big">검색 결과가 없어요</div>다른 키워드로 시도해 보세요.
      </div>
    </template>
  </div>
</template>

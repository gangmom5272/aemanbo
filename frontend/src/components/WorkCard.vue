<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { animeGradient, mangaColor, realImage, animeStatusBadge, statusBadge, ratingText } from '../utils/cover'

const props = defineProps({
  work: { type: Object, required: true },
  kind: { type: String, required: true }, // 'anime' | 'manga'
  rank: { type: Number, default: 0 },
  variant: { type: String, default: 'grid' }, // 'row' | 'grid'
  caption: { type: String, default: '' }, // row 변형에서 평점 대신 표시할 문구
})

const router = useRouter()
const isAnime = computed(() => props.kind === 'anime')

const img = computed(() =>
  realImage(isAnime.value ? props.work.poster_image_url : props.work.cover_image_url)
)
const gradient = computed(() => animeGradient(props.work.title))
const bandColor = computed(() => mangaColor(props.work.title))
const badge = computed(() =>
  isAnime.value ? animeStatusBadge(props.work.status) : statusBadge(props.work.status)
)
const sub = computed(() => {
  if (isAnime.value && props.work.release_year) return String(props.work.release_year)
  return ''
})

function open() {
  router.push({ name: isAnime.value ? 'anime-detail' : 'manga-detail', params: { id: props.work.id } })
}
</script>

<template>
  <article :class="variant === 'row' ? 'wcard' : 'gcard'" @click="open">
    <div class="cover-art" :class="isAnime ? 'cv-anime' : 'cv-manga'" :style="isAnime ? { background: gradient } : null">
      <img v-if="img" class="real" :src="img" :alt="work.title" />
      <span v-if="rank" class="rank">{{ rank }}</span>
      <span class="stat-badge" :class="badge.cls">{{ badge.label }}</span>
      <span v-if="isAnime" class="ct">{{ work.title }}</span>
      <div v-else class="mband" :style="{ background: bandColor }">{{ work.title }}</div>
    </div>

    <template v-if="variant === 'row'">
      <div class="cardinfo">
        <div class="n">{{ work.title }}</div>
        <div v-if="caption" class="m" style="color:var(--spot-deep);font-weight:600;white-space:normal">{{ caption }}</div>
        <div v-else class="m"><span class="star">★</span> {{ ratingText(work.rating_avg) }}<template v-if="sub"> · {{ sub }}</template></div>
      </div>
    </template>
    <template v-else>
      <div class="gtitle">{{ work.title }}</div>
      <div class="gsub"><span class="gstar">★</span> {{ ratingText(work.rating_avg) }}<template v-if="sub"> · {{ sub }}</template></div>
    </template>
  </article>
</template>

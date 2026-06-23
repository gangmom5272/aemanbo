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
    <div class="cover-art" :style="!img ? { background: isAnime ? gradient : bandColor } : null">
      <img v-if="img" class="real" :src="img" :alt="work.title" loading="lazy" />
      <span v-if="rank" class="rank">{{ rank }}</span>
      <span class="stat-badge" :class="badge.cls">{{ badge.label }}</span>
      <div class="cover-title">{{ work.title }}</div>
    </div>

    <template v-if="variant === 'row'">
      <div class="cardinfo">
        <div v-if="caption" class="m cap">{{ caption }}</div>
        <div v-else class="m"><span class="star">★</span> {{ ratingText(work.rating_avg) }}<template v-if="sub"> · {{ sub }}</template></div>
      </div>
    </template>
    <template v-else>
      <div class="gsub"><span class="gstar">★</span> {{ ratingText(work.rating_avg) }}<template v-if="sub"> · {{ sub }}</template></div>
    </template>
  </article>
</template>

<style scoped>
/* 커버 크기/이미지/제목을 컴포넌트 자체에서 강제 → 전역 CSS 상태와 무관하게 항상 동일 */
.cover-art {
  position: relative;
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
  background: var(--surface-2);
}
.cover-art .real {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}
/* 포스터 위 제목 (하단 그라데이션 스크림) */
.cover-art .cover-title {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
  padding: 28px 10px 11px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.45) 55%, transparent);
  color: #fff;
  font-family: 'Black Han Sans', sans-serif;
  font-size: 13.5px;
  line-height: 1.18;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.cardinfo {
  margin-top: 9px;
}
.cardinfo .m.cap {
  color: var(--spot-deep);
  font-weight: 600;
  white-space: normal;
  line-height: 1.35;
}
.gsub {
  margin-top: 9px;
}
</style>

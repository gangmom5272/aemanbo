<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { oauthCallback } from '../api'

const route = useRoute()
const router = useRouter()
const message = ref('로그인 처리 중…')

onMounted(async () => {
  const provider = route.params.provider
  const code = route.query.code
  if (!code) {
    message.value = '인증 코드가 없습니다.'
    return
  }
  try {
    const res = await oauthCallback(provider, code.toString())
    message.value = '로그인 성공! 이동 중…'
    // 신규 가입자(혹은 설문 미완료)는 홈으로 → 선호 장르 설문 모달 노출
    const needsSurvey = res && (res.created || (res.user && !res.user.onboarded))
    setTimeout(() => router.replace(needsSurvey ? '/' : '/mypage'), 600)
  } catch (e) {
    message.value = '로그인에 실패했어요. 다시 시도해 주세요.'
    setTimeout(() => router.replace('/login'), 1500)
  }
})
</script>

<template>
  <div style="min-height:100vh;display:grid;place-items:center">
    <div class="state-msg"><div class="big">{{ message }}</div></div>
  </div>
</template>

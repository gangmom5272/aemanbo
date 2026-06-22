<script setup>
// AI 추천 챗봇은 3차(백엔드 미구현) 기능. URL 스텁: POST /api/v1/chat/message/
function onClick() {
  alert('AI 추천 챗봇은 3차 기능이에요 :) (백엔드 연동 예정)')
}
</script>

<template>
  <button class="fab" @click="onClick">
    <span class="ai">✦</span>
    <span style="display:flex;flex-direction:column;align-items:flex-start;line-height:1.1">
      <span>뭐 볼지 물어보기</span>
      <span style="font-size:10px;font-weight:400;opacity:.9;font-family:'Space Mono',monospace">AI 추천</span>
    </span>
  </button>
</template>

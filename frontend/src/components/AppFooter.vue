<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <footer>
    <div class="foot">
      <span class="logo" @click="router.push('/')">
        <span class="word" style="font-size:18px">애<b>만</b>보</span>
      </span>
      <div class="fl"><a>소개</a><a>이용약관</a><a>개인정보처리방침</a></div>
      <span>© 2026 애만보. All rights reserved.</span>
    </div>
  </footer>
</template>

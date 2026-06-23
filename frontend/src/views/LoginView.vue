<script setup>
import { useRouter } from 'vue-router'
import { getOAuthUrl } from '../api'

const router = useRouter()

async function login(provider) {
  try {
    const data = await getOAuthUrl(provider)
    if (data.authorization_url) {
      window.location.href = data.authorization_url
    }
  } catch (e) {
    if (e.status === 500) {
      alert(`${provider} 로그인 키가 아직 설정되지 않았어요.\n백엔드 .env에 OAuth client_id/secret을 넣어주세요.`)
    } else {
      alert('로그인 URL을 가져오지 못했어요.')
    }
  }
}
</script>

<template>
  <section class="login-shell">
    <div class="brand-panel">
      <div class="logo" style="position:relative;z-index:1"><span class="glyph"></span><span class="word" style="font-size:23px">애<b>만</b>보</span></div>
      <div class="bp-mid">
        <h1>애니 다음은,<br /><span class="accent">원작에서.</span></h1>
        <p>애니가 멈춘 바로 그 장면부터 원작 만화 몇 권 몇 화인지, 애만보가 정확히 짚어드려요.</p>
      </div>
      <div class="bp-foot">© 2026 애만보 — 모든 매핑 정보는 검수 후 제공됩니다.</div>
    </div>
    <div class="auth-panel">
      <div class="auth-card">
        <div class="hi">반가워요!</div>
        <p class="sub">3초면 시작할 수 있어요.<br />소셜 계정으로 바로 들어가세요.</p>
        <div class="social">
          <button class="sbtn kakao" @click="login('kakao')"><span class="ic"><svg width="20" height="20" viewBox="0 0 24 24" fill="#191600"><path d="M12 3C6.5 3 2 6.5 2 10.8c0 2.8 1.9 5.2 4.7 6.6-.2.7-.7 2.6-.8 3-.1.5.2.5.4.4.2-.1 2.6-1.8 3.7-2.5.6.1 1.3.1 2 .1 5.5 0 10-3.5 10-7.8C22 6.5 17.5 3 12 3z"/></svg></span>카카오로 시작하기</button>
          <button class="sbtn naver" @click="login('naver')"><span class="ic">N</span>네이버로 시작하기</button>
          <button class="sbtn google" @click="login('google')"><span class="ic"><svg width="19" height="19" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.5 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2.1-2 3.2-4.9 3.2-7.8z"/><path fill="#34A853" d="M12 23c2.9 0 5.4-1 7.2-2.6l-3.6-2.7c-1 .7-2.3 1.1-3.6 1.1-2.8 0-5.1-1.9-6-4.4H2.3v2.8A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M6 14.4a6.6 6.6 0 0 1 0-4.2V7.4H2.3a11 11 0 0 0 0 9.8L6 14.4z"/><path fill="#EA4335" d="M12 5.5c1.6 0 3 .5 4.1 1.6l3.1-3.1A11 11 0 0 0 12 1a11 11 0 0 0-9.7 6l3.7 2.8c.9-2.6 3.2-4.3 6-4.3z"/></svg></span>Google로 계속하기</button>
        </div>
        <div class="auth-alt">먼저 둘러볼까요? <a @click="router.push('/')">홈으로</a></div>
        <div class="auth-terms">계속 진행하면 애만보의 <a>이용약관</a> 및 <a>개인정보처리방침</a>에<br />동의하게 됩니다.</div>
      </div>
    </div>
  </section>
</template>

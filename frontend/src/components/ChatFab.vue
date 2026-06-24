<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { sendChatMessage, clearChatSession } from '../api'
import { animeGradient, mangaColor, realImage } from '../utils/cover'

const router = useRouter()
const open = ref(false)
const input = ref('')
const loading = ref(false)
const listEl = ref(null)

const GREETING = { role: 'bot', text: '안녕하세요! 기분이나 상황을 자유롭게 적어주세요. 예: "주술회전 비슷한 거", "잔잔한 일상물 보고 싶어", "울고 싶은 날 볼 작품"', recs: [] }
const messages = ref([GREETING])

function toggle() {
  open.value = !open.value
}

async function scrollDown() {
  await nextTick()
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  scrollDown()
  try {
    const data = await sendChatMessage(text)
    messages.value.push({ role: 'bot', text: data.reply || '추천을 찾지 못했어요.', recs: data.recommendations || [] })
  } catch (e) {
    const msg = (e.data && e.data.detail) || e.message || 'AI 응답에 실패했어요. 잠시 후 다시 시도해 주세요.'
    messages.value.push({ role: 'bot', text: msg, recs: [] })
  } finally {
    loading.value = false
    scrollDown()
  }
}

async function reset() {
  try { await clearChatSession() } catch (_) {}
  messages.value = [GREETING]
}

function openRec(r) {
  open.value = false
  router.push({ name: r.type === 'anime' ? 'anime-detail' : 'manga-detail', params: { id: r.id } })
}
function recImg(r) {
  return realImage(r.poster_image_url || r.cover_image_url)
}
function recStyle(r) {
  return r.type === 'anime' ? { background: animeGradient(r.title) } : { background: mangaColor(r.title) }
}
</script>

<template>
  <div>
    <div v-if="open" class="chat-panel">
      <div class="chat-head">
        <div class="chat-title"><span class="ai-dot">✦</span> AI 추천</div>
        <div class="chat-head-btns">
          <button class="chat-ico" title="대화 초기화" @click="reset">↺</button>
          <button class="chat-ico" title="닫기" @click="toggle">✕</button>
        </div>
      </div>

      <div ref="listEl" class="chat-list">
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble">{{ m.text }}</div>
          <div v-if="m.recs && m.recs.length" class="recs">
            <div v-for="r in m.recs" :key="r.type + '-' + r.id" class="rec" @click="openRec(r)">
              <div class="rec-cover" :style="recStyle(r)">
                <img v-if="recImg(r)" :src="recImg(r)" :alt="r.title" />
              </div>
              <div class="rec-title">{{ r.title }}</div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="msg bot"><div class="bubble">추천 고르는 중…</div></div>
      </div>

      <div class="chat-input">
        <input v-model="input" placeholder="무엇을 찾으세요?" :disabled="loading" @keyup.enter="send" />
        <button :disabled="loading" @click="send">전송</button>
      </div>
    </div>

    <button class="fab" @click="toggle">
      <span class="ai">✦</span>
      <span style="display:flex;flex-direction:column;align-items:flex-start;line-height:1.1">
        <span>뭐 볼지 물어보기</span>
        <span style="font-size:10px;font-weight:400;opacity:.9;font-family:'Space Mono',monospace">AI 추천</span>
      </span>
    </button>
  </div>
</template>

<style scoped>
.chat-panel {
  position: fixed;
  right: 26px;
  bottom: 88px;
  z-index: 70;
  width: 360px;
  max-width: calc(100vw - 36px);
  height: 520px;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 30px 70px -24px rgba(40, 20, 70, 0.55);
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 14px;
  background: linear-gradient(120deg, var(--glow), var(--spot));
  color: #fff;
}
.chat-title {
  font-family: 'Black Han Sans', sans-serif;
  font-size: 16px;
}
.ai-dot {
  margin-right: 4px;
}
.chat-head-btns {
  display: flex;
  gap: 6px;
}
.chat-ico {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}
.chat-ico:hover {
  background: rgba(255, 255, 255, 0.35);
}
.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--bg);
}
.msg {
  display: flex;
  flex-direction: column;
  max-width: 100%;
}
.msg.user {
  align-items: flex-end;
}
.bubble {
  font-size: 14px;
  line-height: 1.5;
  padding: 10px 13px;
  border-radius: 14px;
  white-space: pre-wrap;
  max-width: 85%;
}
.msg.bot .bubble {
  background: var(--surface);
  border: 1px solid var(--line-2);
  color: var(--ink-soft);
  border-top-left-radius: 4px;
}
.msg.user .bubble {
  background: linear-gradient(120deg, var(--glow), var(--spot));
  color: #fff;
  border-top-right-radius: 4px;
}
.recs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  margin-top: 10px;
  padding-bottom: 4px;
}
.rec {
  flex: 0 0 84px;
  cursor: pointer;
}
.rec-cover {
  position: relative;
  width: 84px;
  aspect-ratio: 3 / 4;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
.rec-cover img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.rec-title {
  font-size: 11.5px;
  font-weight: 500;
  margin-top: 5px;
  line-height: 1.25;
  color: var(--ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--line);
  background: var(--surface);
}
.chat-input input {
  flex: 1;
  height: 40px;
  border: 1px solid var(--line-2);
  border-radius: 11px;
  padding: 0 13px;
  font-family: inherit;
  font-size: 14px;
  background: var(--surface-2);
  outline: none;
}
.chat-input input:focus {
  border-color: var(--glow);
}
.chat-input button {
  height: 40px;
  padding: 0 16px;
  border: none;
  border-radius: 11px;
  background: var(--ink);
  color: #fff;
  font-family: inherit;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}
.chat-input button:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>

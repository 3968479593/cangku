<template>
  <div class="chat-page">
    <div class="page-header">
      <h2>💬 AI 选品分析</h2>
      <p class="desc">基于知识库中的商品数据，AI 给出有数据支撑的选品建议</p>
    </div>

    <div class="chat-box">
      <div class="chat-topbar">
        <span class="conv-id" v-if="conversationId">
          <span class="dot"></span>会话 {{ conversationId.slice(0, 8) }}...
        </span>
        <span v-else class="conv-id"><span class="dot idle"></span>新会话</span>
        <button class="btn-clear" @click="doClear" :disabled="!messages.length">🗑 清空对话</button>
      </div>

      <div class="chat-messages" ref="chatBox">
        <div v-if="!messages.length" class="chat-hint">
          <div class="hint-ico">💬</div>
          <p>输入选品需求，AI 将基于商品数据给出分析建议</p>
          <div class="hint-tags">
            <span v-for="q in hints" :key="q" class="hint-tag" @click="askAI(q)">{{ q }}</span>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div class="msg-bubble-wrap">
            <details v-if="msg.role === 'assistant' && msg.reasoning" class="reasoning-box" open>
              <summary>🧠 深度思考过程</summary>
              <div class="reasoning-text">{{ msg.reasoning }}</div>
            </details>
            <div v-if="msg.content" class="msg-text">{{ msg.content }}</div>
            <div v-else-if="msg.role === 'assistant' && chatLoading" class="msg-text thinking">
              <span class="dots"><i></i><i></i><i></i></span>思考中
            </div>
          </div>
        </div>

        <div
          v-if="chatLoading && (!messages.length || messages[messages.length - 1].role !== 'assistant')"
          class="msg assistant"
        >
          <div class="msg-bubble-wrap">
            <div class="msg-text thinking"><span class="dots"><i></i><i></i><i></i></span>思考中</div>
          </div>
        </div>
      </div>

      <div v-if="batchReport" class="batch-tools">
        <button class="btn-word" @click="doExportWord" :disabled="exporting">
          {{ exporting ? '导出中...' : '📄 导出 Word 报告' }}
        </button>
      </div>

      <!-- AI 追问满意度，反馈上传给管理员 -->
      <div v-if="batchReport && !feedbackSubmitted" class="feedback-card">
        <div class="fb-title">💬 以上批量分析已完成，您对本次分析是否满意？</div>
        <div class="fb-choices">
          <button :class="['fb-choice', { active: feedbackForm.satisfaction === true }]" @click="feedbackForm.satisfaction = true">😊 满意</button>
          <button :class="['fb-choice', { active: feedbackForm.satisfaction === false }]" @click="feedbackForm.satisfaction = false">😞 不满意</button>
        </div>
        <textarea v-model="feedbackForm.comment" class="fb-input" rows="2" placeholder="补充意见（可选）"></textarea>
        <button class="fb-submit" @click="submitFeedback" :disabled="submitting || feedbackForm.satisfaction === null">
          {{ submitting ? '提交中...' : '提交反馈' }}
        </button>
      </div>
      <div v-else-if="feedbackSubmitted" class="feedback-card fb-done">✓ 感谢您的反馈！</div>

      <div class="chat-input-row">
        <button
          class="btn-think"
          :class="{ active: deepThinking }"
          @click="deepThinking = !deepThinking"
          :title="deepThinking ? '深度思考已开启' : '开启深度思考'"
        >🧠 深度思考</button>
        <input
          v-model="chatInput"
          class="chat-input"
          placeholder="输入选品问题..."
          @keyup.enter="askAI(chatInput)"
        />
        <button class="btn-send" @click="askAI(chatInput)" :disabled="chatLoading">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, authFetch } from '../api'
import { selectedList } from '../selected'

const chatInput = ref('')
const messages = ref([])
const chatLoading = ref(false)
const chatBox = ref(null)
const conversationId = ref('')
const deepThinking = ref(false)
const batchReport = ref('')
const exporting = ref(false)
const feedbackForm = reactive({ satisfaction: null, comment: '' })
const feedbackSubmitted = ref(false)
const submitting = ref(false)

const route = useRoute()
const router = useRouter()

const hints = [
  '最近什么品类销量最好？',
  '帮我分析家居品类的选品趋势',
  '推荐几个高利润潜力的商品',
]

function pushAssistant() {
  const msg = reactive({ role: 'assistant', content: '', reasoning: '' })
  messages.value.push(msg)
  return msg
}

async function askAI(text) {
  const q = (typeof text === 'string' ? text : chatInput.value).trim()
  if (!q) return
  if (typeof text === 'string') chatInput.value = ''
  messages.value.push({ role: 'user', content: q })
  chatLoading.value = true

  let assistantMsg = null
  try {
    const res = await authFetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: q,
        conversation_id: conversationId.value || null,
        deep_thinking: deepThinking.value,
      }),
    })
    if (res.status === 401) throw new Error('未登录')
    if (!res.ok) throw new Error('HTTP ' + res.status)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 2)
        if (!rawEvent.startsWith('data:')) continue
        const payload = rawEvent.slice(5).trim()
        if (!payload) continue
        let data
        try { data = JSON.parse(payload) } catch { continue }

        if (data.type === 'reasoning') {
          if (!assistantMsg) assistantMsg = pushAssistant()
          assistantMsg.reasoning += data.delta
        } else if (data.type === 'content') {
          if (!assistantMsg) assistantMsg = pushAssistant()
          assistantMsg.content += data.delta
        } else if (data.type === 'done') {
          conversationId.value = data.conversation_id
        } else if (data.type === 'error') {
          if (!assistantMsg) assistantMsg = pushAssistant()
          assistantMsg.content += (assistantMsg.content ? '\n' : '') + (data.message || '生成失败')
        }
        // data.type === 'sources' 暂不渲染，仅保留后续展示能力
      }
    }

    if (assistantMsg && !assistantMsg.content && !assistantMsg.reasoning) {
      assistantMsg.content = '未获取到回复'
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '请求失败，请确认后端服务已启动' })
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

async function doClear() {
  if (conversationId.value) {
    await api.del(`/api/chat/conversation/${conversationId.value}`)
  }
  messages.value = []
  conversationId.value = ''
  batchReport.value = ''
}

// ---- 批量分析选定商品（从检索页跳转进入） ----
async function doBatchAnalysis() {
  const products = selectedList.value
  if (!products.length) return
  chatLoading.value = true
  const summary = products.map((p, i) =>
    `${i + 1}. ${p.name}（¥${p.price}｜销量${p.sales_volume}｜评分${p.rating}）`
  ).join('\n')
  messages.value.push({ role: 'user', content: `请对我选定的 ${products.length} 件商品进行批量分析：\n${summary}` })

  const assistantMsg = reactive({ role: 'assistant', content: '', reasoning: '' })
  messages.value.push(assistantMsg)
  batchReport.value = ''
  feedbackSubmitted.value = false
  feedbackForm.satisfaction = null
  feedbackForm.comment = ''

  try {
    const res = await authFetch('/api/analysis/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products, deep_thinking: deepThinking.value }),
    })
    if (res.status === 401) throw new Error('未登录')
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 2)
        if (!rawEvent.startsWith('data:')) continue
        const payload = rawEvent.slice(5).trim()
        if (!payload) continue
        let data
        try { data = JSON.parse(payload) } catch { continue }
        if (data.type === 'content') {
          assistantMsg.content += data.delta
          batchReport.value += data.delta
        } else if (data.type === 'error') {
          assistantMsg.content += (assistantMsg.content ? '\n' : '') + (data.message || '分析失败')
        }
      }
    }
    if (!assistantMsg.content) assistantMsg.content = '未获取到分析结果'
  } catch (e) {
    assistantMsg.content = '分析请求失败：' + (e.message || '请确认后端服务已启动')
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

// ---- 导出批量分析报告为 Word ----
async function doExportWord() {
  if (!batchReport.value || exporting.value) return
  exporting.value = true
  try {
    const res = await authFetch('/api/analysis/export-docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report: batchReport.value,
        products: selectedList.value,
        title: '选定商品批量分析报告',
      }),
    })
    if (res.status === 401) throw new Error('未登录')
    if (!res.ok) throw new Error('导出失败')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '选定商品分析报告.docx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

// ---- 提交分析反馈（上传给管理员）----
async function submitFeedback() {
  if (feedbackForm.satisfaction === null) {
    alert('请选择满意或不满意')
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const res = await authFetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report: batchReport.value,
        products_summary: selectedList.value.map((p, i) => `${i + 1}.${p.name}`).join('；'),
        product_count: selectedList.value.length,
        satisfaction: feedbackForm.satisfaction,
        comment: feedbackForm.comment,
      }),
    })
    if (res.status === 401) throw new Error('未登录')
    if (!res.ok) throw new Error('提交失败')
    feedbackSubmitted.value = true
  } catch (e) {
    alert(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 从检索页跳转进入时自动发起批量分析
// 用 watch 监听 query：keep-alive 缓存组件时 onMounted 仅首次触发，会漏掉后续跳转
watch(() => route.query.batch, (val) => {
  if (val !== '1') return
  router.replace({ path: '/chat' })  // 去掉 query，防刷新/重复触发
  if (selectedList.value.length > 0) {
    doBatchAnalysis()
  } else {
    messages.value.push({ role: 'assistant', content: '尚未选定商品。请先在「商品检索」页选定商品后，再使用 AI 批量分析。' })
  }
}, { immediate: true })
</script>

<style scoped>
.page-header { margin-bottom: 22px; }
.page-header h2 {
  font-size: 22px; color: var(--text); margin: 0 0 6px; font-weight: 800;
  padding-left: 12px; border-left: 4px solid var(--primary);
}
.desc { color: var(--text-mute); font-size: 14px; margin: 0; padding-left: 16px; }

.chat-box {
  background: #fff; border-radius: var(--radius-lg); overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.chat-topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid var(--border); font-size: 13px;
  background: var(--bg-soft);
}
.conv-id { color: var(--text-mute); display: inline-flex; align-items: center; gap: 7px; font-weight: 500; }
.conv-id .dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-green); box-shadow: 0 0 0 3px rgba(54,196,143,.18);
}
.conv-id .dot.idle { background: var(--text-mute); box-shadow: 0 0 0 3px rgba(154,163,178,.2); }
.btn-clear {
  padding: 6px 16px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; color: var(--text-sub);
  transition: all .2s;
}
.btn-clear:hover:not(:disabled) { background: #fff5f5; border-color: var(--accent-red); color: var(--accent-red); }
.btn-clear:disabled { opacity: .4; cursor: not-allowed; }

.chat-messages { padding: 26px; min-height: 480px; max-height: calc(100vh - 240px); overflow-y: auto; }

.chat-hint { text-align: center; padding: 90px 0; color: var(--text-mute); }
.hint-ico { font-size: 52px; opacity: .35; margin-bottom: 18px; }
.chat-hint p { margin-bottom: 18px; font-size: 14px; }
.hint-tags { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.hint-tag {
  padding: 8px 18px; background: var(--primary-50); color: var(--primary-dark);
  border: 1px solid var(--primary-light); border-radius: 999px;
  font-size: 13px; cursor: pointer; transition: all .2s;
}
.hint-tag:hover { background: var(--primary-grad); color: #fff; border-color: transparent; box-shadow: var(--shadow-primary); }

/* 消息行 */
.msg {
  margin-bottom: 18px;
  display: flex;
}
.msg.user { justify-content: flex-end; }
.msg-bubble-wrap { max-width: 75%; }
.msg.user .msg-bubble-wrap { display: flex; flex-direction: column; align-items: flex-end; }

.msg-text {
  background: var(--bg-soft); padding: 11px 16px; border-radius: var(--radius);
  font-size: 14px; line-height: 1.7; color: var(--text);
  border: 1px solid var(--border);
  white-space: pre-wrap; word-break: break-word;
}
.msg.user .msg-text {
  background: var(--primary-grad); color: #fff; border: none;
  box-shadow: var(--shadow-primary);
  border-radius: var(--radius) var(--radius-sm) var(--radius) var(--radius);
}
.msg.assistant .msg-text {
  border-radius: var(--radius-sm) var(--radius) var(--radius) var(--radius);
}
.thinking { color: var(--text-mute) !important; background: #fff !important; font-style: italic; }

/* 思考中三点动画 */
.dots { display: inline-flex; gap: 3px; margin-right: 4px; }
.dots i {
  width: 5px; height: 5px; border-radius: 50%; background: var(--primary);
  animation: bounce-dot 1.2s infinite ease-in-out;
}
.dots i:nth-child(2) { animation-delay: .15s; }
.dots i:nth-child(3) { animation-delay: .3s; }
@keyframes bounce-dot {
  0%, 80%, 100% { transform: scale(.6); opacity: .5; }
  40% { transform: scale(1); opacity: 1; }
}

.batch-tools { display: flex; justify-content: center; padding: 12px 20px 0; background: var(--bg-soft); }
.btn-word {
  padding: 8px 22px; border-radius: 999px; cursor: pointer; font-size: 13px; font-weight: 600;
  background: #fff; border: 1px solid #2e7d32; color: #2e7d32; transition: all .2s;
  box-shadow: 0 2px 8px rgba(46,125,50,.15);
}
.btn-word:hover:not(:disabled) { background: #2e7d32; color: #fff; }
.btn-word:disabled { opacity: .5; cursor: not-allowed; }

/* 反馈卡：AI 追问满意度 */
.feedback-card {
  margin: 12px 20px 0; padding: 16px 18px;
  background: linear-gradient(135deg, #f0f7ff, #eef2ff);
  border: 1px solid var(--primary-light); border-radius: var(--radius);
}
.feedback-card.fb-done { background: #e8f5e9; border-color: #c8e6c9; color: #2e7d32; text-align: center; font-weight: 600; }
.fb-title { font-size: 14px; color: var(--text); font-weight: 600; margin-bottom: 12px; }
.fb-choices { display: flex; gap: 10px; margin-bottom: 10px; }
.fb-choice {
  flex: 1; padding: 9px; border-radius: var(--radius-sm); cursor: pointer; font-size: 14px; font-weight: 500;
  background: #fff; border: 1px solid var(--border); color: var(--text-sub); transition: all .2s;
}
.fb-choice:hover { border-color: var(--primary); }
.fb-choice.active { background: var(--primary-grad); border-color: transparent; color: #fff; box-shadow: var(--shadow-primary); }
.fb-input {
  width: 100%; padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; outline: none; resize: vertical; font-family: inherit; box-sizing: border-box;
}
.fb-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(18,183,245,.12); }
.fb-submit {
  margin-top: 10px; padding: 9px 22px; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; font-weight: 600;
  background: var(--primary-grad); border: none; color: #fff; box-shadow: var(--shadow-primary); transition: transform .2s;
}
.fb-submit:hover:not(:disabled) { transform: translateY(-1px); }
.fb-submit:disabled { opacity: .5; cursor: not-allowed; }

.chat-input-row { display: flex; gap: 10px; padding: 14px 20px; border-top: 1px solid var(--border); background: var(--bg-soft); }
.chat-input {
  flex: 1; padding: 11px 16px; border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm); font-size: 14px; outline: none; background: #fff; color: var(--text);
  transition: border-color .2s, box-shadow .2s;
}
.chat-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(18,183,245,.12); }
.chat-input::placeholder { color: var(--text-mute); }
.btn-send {
  padding: 11px 26px; background: var(--primary-grad); color: #fff;
  border: none; border-radius: var(--radius-sm); font-size: 14px; cursor: pointer; font-weight: 600;
  box-shadow: var(--shadow-primary); transition: transform .2s;
}
.btn-send:hover:not(:disabled) { transform: translateY(-1px); }
.btn-send:disabled { opacity: .6; cursor: not-allowed; transform: none; box-shadow: none; }

.btn-think {
  padding: 11px 16px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; color: var(--text-sub);
  white-space: nowrap; transition: all .2s; font-weight: 500;
}
.btn-think:hover { border-color: var(--accent-purple); color: var(--accent-purple); }
.btn-think.active {
  background: linear-gradient(135deg, #f3e8ff, #e9e0ff); border-color: var(--accent-purple);
  color: #7c3aed; font-weight: 600; box-shadow: 0 4px 10px rgba(155,107,255,.2);
}

/* 深度思考过程框 */
.reasoning-box {
  margin-bottom: 8px; background: linear-gradient(135deg, #faf8ff, #f5f0ff);
  border: 1px solid #ece4ff; border-radius: var(--radius-sm);
  padding: 10px 14px; font-size: 13px; color: var(--text-sub);
}
.reasoning-box summary {
  cursor: pointer; font-weight: 600; color: #7c3aed; user-select: none;
  list-style: none; display: flex; align-items: center; gap: 4px;
}
.reasoning-box summary::-webkit-details-marker { display: none; }
.reasoning-box summary::before { content: '▸'; font-size: 12px; transition: transform .2s; }
.reasoning-box[open] summary::before { transform: rotate(90deg); }
.reasoning-text {
  margin-top: 8px; line-height: 1.65; white-space: pre-wrap; color: var(--text-sub);
  padding-top: 8px; border-top: 1px dashed #ece4ff;
}
</style>

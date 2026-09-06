<template>
  <div class="manage-feedback">
    <h2 class="section-title">💬 用户反馈</h2>

    <div class="feedback-module">
      <div class="fb-stats" v-if="feedback.total > 0">
        <div class="fb-stat"><div class="num">{{ feedback.total }}</div><div class="lbl">总反馈</div></div>
        <div class="fb-stat ok"><div class="num">{{ feedback.satisfied }}</div><div class="lbl">满意</div></div>
        <div class="fb-stat bad"><div class="num">{{ feedback.unsatisfied }}</div><div class="lbl">不满意</div></div>
        <div class="fb-stat"><div class="num">{{ feedback.satisfaction_rate }}%</div><div class="lbl">满意率</div></div>
      </div>

      <div class="list-head">
        <h3>反馈列表</h3>
        <button class="btn-refresh" @click="loadFeedback" :disabled="loadingFeedback">
          {{ loadingFeedback ? '加载中...' : '↻ 刷新' }}
        </button>
      </div>

      <div class="list-empty" v-if="!loadingFeedback && feedback.items.length === 0">暂无用户反馈</div>

      <div class="fb-row" v-for="f in feedback.items" :key="f.id">
        <div class="fb-row-head">
          <span class="fb-user">{{ f.user_nickname || f.user_account || '匿名' }}</span>
          <span :class="['fb-tag', f.satisfaction ? 'ok' : 'bad']">{{ f.satisfaction ? '😊 满意' : '😞 不满意' }}</span>
          <span class="fb-count">{{ f.product_count }} 件商品</span>
          <span class="fb-time">{{ f.created_at }}</span>
          <button class="fb-toggle" @click="toggleFb(f.id)">{{ openFb === f.id ? '收起' : '查看报告' }}</button>
          <button class="fb-del" @click="onDelete(f)" :disabled="deletingFb === f.id">{{ deletingFb === f.id ? '删除中' : '删除' }}</button>
        </div>
        <div class="fb-comment" v-if="f.comment">📋 意见：{{ f.comment }}</div>
        <pre class="fb-report" v-if="openFb === f.id">{{ f.report }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'

const feedback = reactive({ total: 0, satisfied: 0, unsatisfied: 0, satisfaction_rate: 0, items: [] })
const loadingFeedback = ref(false)
const openFb = ref(null)
const deletingFb = ref(null)

onMounted(loadFeedback)

async function loadFeedback() {
  loadingFeedback.value = true
  try {
    const res = await api.get('/api/admin/feedback')
    const data = await res.json()
    if (res.ok) Object.assign(feedback, data)
  } catch (e) { /* ignore */ } finally {
    loadingFeedback.value = false
  }
}

function toggleFb(id) {
  openFb.value = openFb.value === id ? null : id
}

async function onDelete(f) {
  if (!confirm('确认删除该条反馈？此操作不可恢复。')) return
  deletingFb.value = f.id
  try {
    const res = await api.del(`/api/admin/feedback/${f.id}`)
    if (res.ok) {
      await loadFeedback()  // 删除后重新拉取统计 + 列表
    } else {
      const data = await res.json()
      alert(data.detail || '删除失败')
    }
  } catch (e) {
    alert(e.message || '网络错误')
  } finally {
    deletingFb.value = null
  }
}
</script>

<style scoped>
.section-title {
  font-size: 20px; color: var(--text); margin-bottom: 20px;
  padding-left: 12px; border-left: 4px solid var(--primary); font-weight: 700;
}

.feedback-module {
  background: #fff; border-radius: 12px; padding: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,.05);
}
.fb-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.fb-stat { text-align: center; padding: 14px 8px; border-radius: 10px; background: #f5f7fa; border: 1px solid #eef0f3; }
.fb-stat.ok { background: #e8f5e9; border-color: #c8e6c9; }
.fb-stat.bad { background: #ffebee; border-color: #ffcdd2; }
.fb-stat .num { font-size: 24px; font-weight: 700; color: var(--text); }
.fb-stat.ok .num { color: #2e7d32; }
.fb-stat.bad .num { color: #c62828; }
.fb-stat .lbl { font-size: 12px; color: var(--text-mute); margin-top: 4px; }

.list-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-head h3 { font-size: 16px; color: var(--text); font-weight: 600; }
.btn-refresh { padding: 6px 14px; background: #fff; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; color: #666; cursor: pointer; }
.btn-refresh:hover:not(:disabled) { background: #f5f5f5; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }
.list-empty { text-align: center; color: #999; padding: 40px 20px; font-size: 14px; }

.fb-row { padding: 14px; border-radius: 8px; transition: background .15s; }
.fb-row:hover { background: #f9fafb; }
.fb-row + .fb-row { border-top: 1px solid #f0f0f0; }
.fb-row-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.fb-user { font-size: 14px; font-weight: 600; color: var(--text); }
.fb-tag { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.fb-tag.ok { color: #2e7d32; background: #e8f5e9; }
.fb-tag.bad { color: #c62828; background: #ffebee; }
.fb-count { font-size: 12px; color: var(--text-mute); }
.fb-time { font-size: 12px; color: var(--text-mute); margin-left: auto; }
.fb-toggle { padding: 4px 12px; background: #fff; border: 1px solid var(--primary); color: var(--primary); border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .2s; }
.fb-toggle:hover { background: var(--primary); color: #fff; }
.fb-del { padding: 4px 12px; background: #fff; border: 1px solid #f56c6c; color: #f56c6c; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .2s; }
.fb-del:hover:not(:disabled) { background: #f56c6c; color: #fff; }
.fb-del:disabled { opacity: .5; cursor: not-allowed; }
.fb-comment { margin-top: 8px; padding: 8px 12px; background: #f5f7fa; border-radius: 6px; font-size: 13px; color: var(--text-sub); }
.fb-report {
  margin: 10px 0 0; padding: 14px; background: #f5f7fa; border: 1px solid #eef0f3;
  border-radius: 8px; max-height: 360px; overflow-y: auto;
  font-family: -apple-system, "Microsoft YaHei", sans-serif;
  font-size: 13px; line-height: 1.7; color: var(--text);
  white-space: pre-wrap; word-break: break-word;
}
</style>

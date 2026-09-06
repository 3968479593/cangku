<template>
  <div class="admin-layout">
    <!-- 顶栏 -->
    <header class="admin-header">
      <div class="brand">
        <span class="logo">🛡</span>
        <div>
          <div class="title">管理后台</div>
          <div class="sub">AI 电商选品助手</div>
        </div>
      </div>

      <div class="admin-user" v-if="adminState.admin" @click="openPanel = !openPanel" v-click-outside="closePanel">
        <div class="avatar">{{ (adminState.admin.username || '?')[0] }}</div>
        <span class="name">{{ adminState.admin.username }}</span>
        <span class="caret">▾</span>

        <transition name="pop">
          <div class="panel" v-if="openPanel" @click.stop>
            <div class="panel-head">
              <div class="avatar lg">{{ (adminState.admin.username || '?')[0] }}</div>
              <div>
                <div class="p-name">{{ adminState.admin.username }}</div>
                <div class="p-role">角色：{{ adminState.admin.role }}</div>
              </div>
            </div>
            <div class="panel-body">
              <div class="row" v-if="adminState.admin.last_login">
                <span class="k">最近登录</span>
                <span class="v">{{ adminState.admin.last_login.slice(0, 19).replace('T', ' ') }}</span>
              </div>
              <div class="row">
                <span class="k">注册时间</span>
                <span class="v">{{ adminState.admin.created_at?.slice(0, 10) }}</span>
              </div>
            </div>
            <div class="panel-foot">
              <button class="btn-logout" @click="onLogout">退出登录</button>
            </div>
          </div>
        </transition>
      </div>
    </header>

    <!-- 主体 -->
    <main class="admin-main">
      <div class="container">
        <h2 class="section-title">📄 文档管理</h2>

        <!-- 上传区 -->
        <div class="upload-card">
          <h3>上传新文档</h3>
          <p class="tip">支持 PDF / CSV / XLSX / XLS / TXT，单个文件最大 50MB</p>

          <div
            class="drop-zone"
            :class="{ dragging, hasFile: selectedFile }"
            @click="$refs.fileInput.click()"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
          >
            <input ref="fileInput" type="file" hidden
              accept=".pdf,.csv,.xlsx,.xls,.txt"
              @change="onFileChange" />
            <template v-if="!selectedFile">
              <div class="dz-icon">⬆</div>
              <div class="dz-text">点击选择文件或拖拽到此处</div>
              <div class="dz-hint">支持 PDF / TXT 文档 · 商品 CSV/Excel 自动导入并更新看板</div>
            </template>
            <template v-else>
              <div class="dz-icon ok">📄</div>
              <div class="dz-text">
                <strong>{{ selectedFile.name }}</strong>
                <span class="size">（{{ formatSize(selectedFile.size) }}）</span>
              </div>
            </template>
          </div>

          <div class="upload-actions">
            <button class="btn-upload" :disabled="!selectedFile || uploading" @click="onUpload">
              {{ uploading ? `上传中 ${uploadProgress}%` : '开始上传并解析' }}
            </button>
            <button class="btn-clear" v-if="selectedFile && !uploading" @click="clearFile">清除</button>
          </div>
          <div class="progress-bar" v-if="uploading">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>

          <transition name="msg-fade">
            <div v-if="uploadMsg" :class="['msg', uploadOk ? 'ok' : 'err']">
              <span class="msg-icon">{{ uploadOk ? '✓' : '✕' }}</span>
              {{ uploadMsg }}
            </div>
          </transition>
        </div>

        <!-- 文档列表 -->
        <div class="list-card">
          <div class="list-head">
            <h3>已上传文档</h3>
            <button class="btn-refresh" @click="loadDocs" :disabled="loadingList">
              {{ loadingList ? '加载中...' : '↻ 刷新' }}
            </button>
          </div>

          <div class="list-empty" v-if="!loadingList && docs.length === 0">
            还没有文档，上传第一个吧
          </div>

          <div class="doc-item" v-for="d in docs" :key="d.id">
            <div class="doc-icon" :class="d.file_type">📄</div>
            <div class="doc-info">
              <div class="doc-name">{{ d.filename }}</div>
              <div class="doc-meta">
                <span class="tag" :class="d.status">{{ statusText(d.status) }}</span>
                <span>类型：{{ d.file_type?.toUpperCase() }}</span>
                <span>切片数：{{ d.chunk_count }}</span>
                <span>{{ d.created_at?.slice(0, 19).replace('T', ' ') }}</span>
              </div>
            </div>
            <button class="btn-del" @click="onDelete(d)" :disabled="deletingId === d.id">
              {{ deletingId === d.id ? '删除中' : '删除' }}
            </button>
          </div>
        </div>

        <!-- 用户反馈 -->
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
            </div>
            <div class="fb-comment" v-if="f.comment">📋 意见：{{ f.comment }}</div>
            <pre class="fb-report" v-if="openFb === f.id">{{ f.report }}</pre>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { adminState, clearAdminAuth } from '../auth'

const router = useRouter()
const openPanel = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMsg = ref('')
const uploadOk = ref(false)

const docs = ref([])
const loadingList = ref(false)
const deletingId = ref(null)

const feedback = reactive({ total: 0, satisfied: 0, unsatisfied: 0, satisfaction_rate: 0, items: [] })
const loadingFeedback = ref(false)
const openFb = ref(null)

onMounted(() => { loadDocs(); loadFeedback() })

async function loadDocs() {
  loadingList.value = true
  try {
    const res = await api.get('/api/documents/')
    const data = await res.json()
    if (res.ok) docs.value = data
  } catch (e) { /* ignore */ } finally {
    loadingList.value = false
  }
}

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

function closePanel() { openPanel.value = false }

function onFileChange(e) {
  const f = e.target.files[0]
  if (f) selectedFile.value = f
}
function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) selectedFile.value = f
}
function clearFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function onUpload() {
  if (!selectedFile.value) return
  uploadMsg.value = ''
  uploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  // 用 XHR 监听上传进度
  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/documents/upload')
  const token = localStorage.getItem('admin_token')
  if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) uploadProgress.value = Math.round((e.loaded / e.total) * 100)
  }

  xhr.onload = () => {
    uploading.value = false
    let data = {}
    try { data = JSON.parse(xhr.responseText) } catch (e) {}
    if (xhr.status >= 200 && xhr.status < 300) {
      uploadOk.value = true
      if (data.type === 'product_import') {
        uploadMsg.value = `商品数据导入成功：${data.filename}，共导入 ${data.product_count} 条商品，看板数据已更新`
      } else {
        uploadMsg.value = `上传成功：${data.filename}，共解析 ${data.chunk_count} 个切片`
      }
      clearFile()
      loadDocs()
    } else {
      uploadOk.value = false
      uploadMsg.value = data.detail || `上传失败（${xhr.status}）`
      if (xhr.status === 401) {
        clearAdminAuth()
        setTimeout(() => router.push('/admin/login'), 800)
      }
    }
  }
  xhr.onerror = () => {
    uploading.value = false
    uploadOk.value = false
    uploadMsg.value = '网络错误，上传失败'
  }
  xhr.send(formData)
}

async function onDelete(d) {
  if (!confirm(`确认删除文档「${d.filename}」？此操作不可恢复。`)) return
  deletingId.value = d.id
  try {
    const res = await api.del(`/api/documents/${d.id}`)
    if (res.ok) {
      docs.value = docs.value.filter(x => x.id !== d.id)
    } else {
      const data = await res.json()
      alert(data.detail || '删除失败')
    }
  } catch (e) {
    alert(e.message || '网络错误')
  } finally {
    deletingId.value = null
  }
}

function onLogout() {
  clearAdminAuth()
  openPanel.value = false
  router.push('/admin/login')
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}
function statusText(s) {
  return { uploaded: '已上传', processing: '处理中', completed: '已完成', failed: '失败' }[s] || s
}

const vClickOutside = {
  mounted(el) {
    el._handler = (e) => { if (!el.contains(e.target)) el.__close?.() }
    el.__close = closePanel
    document.addEventListener('click', el._handler)
  },
  unmounted(el) { document.removeEventListener('click', el._handler) },
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}

/* 顶栏 */
.admin-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .15);
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand .logo { font-size: 28px; }
.brand .title { font-size: 18px; font-weight: 700; letter-spacing: 1px; }
.brand .sub { font-size: 11px; color: #8892b0; }

.admin-user {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  transition: background .2s;
}
.admin-user:hover { background: rgba(255, 255, 255, 0.1); }
.avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #12B7F5, #0D8BD9);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 600;
}
.avatar.lg { width: 50px; height: 50px; font-size: 22px; }
.name { font-size: 14px; }
.caret { font-size: 11px; opacity: .7; }

.panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, .2);
  overflow: hidden;
  z-index: 100;
  color: #333;
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
  color: #fff;
}
.p-name { font-size: 16px; font-weight: 600; }
.p-role { font-size: 12px; opacity: .85; margin-top: 2px; }
.panel-body { padding: 12px 18px; }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: #999; }
.v { color: #333; }
.panel-foot { padding: 12px 18px 16px; }
.btn-logout {
  width: 100%;
  padding: 10px;
  background: #fff;
  border: 1px solid #f56c6c;
  color: #f56c6c;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
}
.btn-logout:hover { background: #f56c6c; color: #fff; }
.pop-enter-active, .pop-leave-active { transition: opacity .15s, transform .15s; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-6px); }

/* 主体 */
.admin-main { flex: 1; padding: 32px 20px 60px; }
.container { max-width: 900px; margin: 0 auto; }
.section-title {
  font-size: 20px;
  color: var(--text);
  margin-bottom: 20px;
  padding-left: 12px;
  border-left: 4px solid var(--primary);
  font-weight: 700;
}

/* 上传卡片 */
.upload-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .05);
}
.upload-card h3 { font-size: 16px; color: var(--text); margin-bottom: 6px; font-weight: 600; }
.upload-card .tip { font-size: 12px; color: var(--text-mute); margin-bottom: 16px; }

.drop-zone {
  border: 2px dashed #d0d7de;
  border-radius: 10px;
  padding: 36px 20px;
  text-align: center;
  cursor: pointer;
  transition: all .2s;
  background: #fafbfc;
}
.drop-zone:hover { border-color: #12B7F5; background: #f0f7ff; }
.drop-zone.dragging { border-color: #12B7F5; background: #e6f4ff; transform: scale(1.01); }
.drop-zone.hasFile { border-style: solid; border-color: #36c48f; background: #f0fdf4; }
.dz-icon { font-size: 36px; margin-bottom: 10px; opacity: .5; }
.dz-icon.ok { opacity: 1; }
.dz-text { font-size: 14px; color: #666; }
.dz-text strong { color: #333; }
.dz-hint { font-size: 12px; color: #999; margin-top: 6px; }
.size { color: #999; margin-left: 6px; }

.upload-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}
.btn-upload {
  padding: 11px 24px;
  background: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}
.btn-upload:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(18, 183, 245, .4); }
.btn-upload:disabled { opacity: .5; cursor: not-allowed; }
.btn-clear {
  padding: 11px 18px;
  background: #fff;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn-clear:hover { background: #f5f5f5; }

.progress-bar {
  margin-top: 12px;
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #12B7F5, #0D8BD9);
  transition: width .2s;
}

.msg {
  margin-top: 14px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
}
.msg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  margin-right: 8px;
  color: #fff;
}
.msg.ok { color: #2e7d32; background: #e8f5e9; }
.msg.ok .msg-icon { background: #4caf50; }
.msg.err { color: #c62828; background: #ffebee; }
.msg.err .msg-icon { background: #f44336; }
.msg-fade-enter-active, .msg-fade-leave-active { transition: all .3s ease; }
.msg-fade-enter-from, .msg-fade-leave-to { opacity: 0; transform: translateY(-6px); }

/* 文档列表 */
.list-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .05);
}
.list-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.list-head h3 { font-size: 16px; color: var(--text); font-weight: 600; }
.btn-refresh {
  padding: 6px 14px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
}
.btn-refresh:hover:not(:disabled) { background: #f5f5f5; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

.list-empty {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 8px;
  transition: background .15s;
}
.doc-item:hover { background: #f9fafb; }
.doc-item + .doc-item { border-top: 1px solid #f0f0f0; }

.doc-icon {
  width: 40px; height: 40px;
  border-radius: 8px;
  background: #f0f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.doc-icon.pdf { background: #ffebee; }
.doc-icon.csv, .doc-icon.xlsx, .doc-icon.xls { background: #e8f5e9; }
.doc-icon.txt { background: #fff3e0; }

.doc-info { flex: 1; min-width: 0; }
.doc-name {
  font-size: 14px;
  color: var(--text);
  font-weight: 600;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
  flex-wrap: wrap;
}
.tag {
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
}
.tag.completed { color: #2e7d32; background: #e8f5e9; }
.tag.processing { color: #f57c00; background: #fff3e0; }
.tag.failed { color: #c62828; background: #ffebee; }
.tag.uploaded { color: #1565c0; background: #e3f2fd; }

.btn-del {
  padding: 6px 14px;
  background: #fff;
  border: 1px solid #f56c6c;
  color: #f56c6c;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all .2s;
}
.btn-del:hover:not(:disabled) { background: #f56c6c; color: #fff; }
.btn-del:disabled { opacity: .5; cursor: not-allowed; }

/* 用户反馈模块 */
.feedback-module {
  background: #fff; border-radius: 12px; padding: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,.05);
}
.fb-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.fb-stat {
  text-align: center; padding: 14px 8px; border-radius: 10px;
  background: #f5f7fa; border: 1px solid #eef0f3;
}
.fb-stat.ok { background: #e8f5e9; border-color: #c8e6c9; }
.fb-stat.bad { background: #ffebee; border-color: #ffcdd2; }
.fb-stat .num { font-size: 24px; font-weight: 700; color: var(--text); }
.fb-stat.ok .num { color: #2e7d32; }
.fb-stat.bad .num { color: #c62828; }
.fb-stat .lbl { font-size: 12px; color: var(--text-mute); margin-top: 4px; }

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
.fb-toggle {
  padding: 4px 12px; background: #fff; border: 1px solid var(--primary);
  color: var(--primary); border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .2s;
}
.fb-toggle:hover { background: var(--primary); color: #fff; }
.fb-comment {
  margin-top: 8px; padding: 8px 12px; background: #f5f7fa; border-radius: 6px;
  font-size: 13px; color: var(--text-sub);
}
.fb-report {
  margin: 10px 0 0; padding: 14px; background: #f5f7fa; border: 1px solid #eef0f3;
  border-radius: 8px; max-height: 360px; overflow-y: auto;
  font-family: -apple-system, "Microsoft YaHei", sans-serif;
  font-size: 13px; line-height: 1.7; color: var(--text);
  white-space: pre-wrap; word-break: break-word;
}

@media (max-width: 640px) {
  .admin-header { padding: 0 16px; }
  .admin-main { padding: 20px 14px 40px; }
  .doc-meta { gap: 8px; }
}
</style>

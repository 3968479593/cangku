<template>
  <div class="manage-docs">
    <h2 class="section-title">📄 文档管理</h2>

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
        <input ref="fileInput" type="file" hidden accept=".pdf,.csv,.xlsx,.xls,.txt" @change="onFileChange" />
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

    <div class="list-card">
      <div class="list-head">
        <h3>已上传文档</h3>
        <button class="btn-refresh" @click="loadDocs" :disabled="loadingList">
          {{ loadingList ? '加载中...' : '↻ 刷新' }}
        </button>
      </div>

      <div class="list-empty" v-if="!loadingList && docs.length === 0">还没有文档，上传第一个吧</div>

      <div class="doc-item" v-for="d in docs" :key="d.id">
        <div class="doc-icon" :class="d.file_type">📄</div>
        <div class="doc-info">
          <div class="doc-name">{{ d.filename }}</div>
          <div class="doc-meta">
            <span class="tag" :class="d.status">{{ statusText(d.status) }}</span>
            <span>类型：{{ d.file_type?.toUpperCase() }}</span>
            <span>条数：{{ d.chunk_count }}</span>
            <span>{{ d.created_at?.slice(0, 19).replace('T', ' ') }}</span>
          </div>
        </div>
        <button class="btn-del" @click="onDelete(d)" :disabled="deletingId === d.id">
          {{ deletingId === d.id ? '删除中' : '删除' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

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

onMounted(loadDocs)

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
      const data = await res.json()
      docs.value = docs.value.filter(x => x.id !== d.id)
      if (data.deleted_products) {
        alert(`删除成功，已清理 ${data.deleted_products} 件关联商品，切回首页可看刷新后的看板`)
      }
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

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}
function statusText(s) {
  return { uploaded: '已上传', processing: '处理中', completed: '已完成', failed: '失败' }[s] || s
}
</script>

<style scoped>
.section-title {
  font-size: 20px; color: var(--text); margin-bottom: 20px;
  padding-left: 12px; border-left: 4px solid var(--primary); font-weight: 700;
}

.upload-card {
  background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,.05);
}
.upload-card h3 { font-size: 16px; color: var(--text); margin-bottom: 6px; font-weight: 600; }
.upload-card .tip { font-size: 12px; color: var(--text-mute); margin-bottom: 16px; }

.drop-zone {
  border: 2px dashed #d0d7de; border-radius: 10px; padding: 36px 20px;
  text-align: center; cursor: pointer; transition: all .2s; background: #fafbfc;
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

.upload-actions { margin-top: 16px; display: flex; gap: 10px; }
.btn-upload {
  padding: 11px 24px; background: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 100%);
  color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all .2s;
}
.btn-upload:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(18,183,245,.4); }
.btn-upload:disabled { opacity: .5; cursor: not-allowed; }
.btn-clear {
  padding: 11px 18px; background: #fff; color: #666; border: 1px solid #ddd;
  border-radius: 8px; font-size: 14px; cursor: pointer;
}
.btn-clear:hover { background: #f5f5f5; }

.progress-bar { margin-top: 12px; height: 6px; background: #eee; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #12B7F5, #0D8BD9); transition: width .2s; }

.msg { margin-top: 14px; padding: 10px 14px; border-radius: 8px; font-size: 13px; display: flex; align-items: center; }
.msg-icon { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 50%; font-size: 11px; font-weight: 700; margin-right: 8px; color: #fff; }
.msg.ok { color: #2e7d32; background: #e8f5e9; }
.msg.ok .msg-icon { background: #4caf50; }
.msg.err { color: #c62828; background: #ffebee; }
.msg.err .msg-icon { background: #f44336; }
.msg-fade-enter-active, .msg-fade-leave-active { transition: all .3s ease; }
.msg-fade-enter-from, .msg-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.list-card { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 10px rgba(0,0,0,.05); }
.list-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-head h3 { font-size: 16px; color: var(--text); font-weight: 600; }
.btn-refresh {
  padding: 6px 14px; background: #fff; border: 1px solid #ddd; border-radius: 6px;
  font-size: 13px; color: #666; cursor: pointer;
}
.btn-refresh:hover:not(:disabled) { background: #f5f5f5; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }
.list-empty { text-align: center; color: #999; padding: 40px 20px; font-size: 14px; }
.doc-item { display: flex; align-items: center; gap: 14px; padding: 14px; border-radius: 8px; transition: background .15s; }
.doc-item:hover { background: #f9fafb; }
.doc-item + .doc-item { border-top: 1px solid #f0f0f0; }
.doc-icon { width: 40px; height: 40px; border-radius: 8px; background: #f0f7ff; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.doc-icon.pdf { background: #ffebee; }
.doc-icon.csv, .doc-icon.xlsx, .doc-icon.xls { background: #e8f5e9; }
.doc-icon.txt { background: #fff3e0; }
.doc-info { flex: 1; min-width: 0; }
.doc-name { font-size: 14px; color: var(--text); font-weight: 600; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-meta { display: flex; gap: 12px; font-size: 12px; color: #999; flex-wrap: wrap; }
.tag { padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.tag.completed { color: #2e7d32; background: #e8f5e9; }
.tag.processing { color: #f57c00; background: #fff3e0; }
.tag.failed { color: #c62828; background: #ffebee; }
.tag.uploaded { color: #1565c0; background: #e3f2fd; }
.btn-del {
  padding: 6px 14px; background: #fff; border: 1px solid #f56c6c; color: #f56c6c;
  border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .2s;
}
.btn-del:hover:not(:disabled) { background: #f56c6c; color: #fff; }
.btn-del:disabled { opacity: .5; cursor: not-allowed; }
</style>

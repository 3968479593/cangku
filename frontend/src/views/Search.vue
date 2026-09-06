<template>
  <div class="search-page">
    <!-- ① 标题 + 说明 -->
    <div class="page-header">
      <h2>🔍 商品检索</h2>
      <p class="desc">输入关键词智能匹配商品，或通过筛选条件精准定位</p>
    </div>

    <!-- 选定（默认隐藏，点击展开，每条可单独删除） -->
    <div class="selected-wrap">
      <button class="sel-toggle" :class="{ has: selectedCount > 0 }" @click="showSelected = !showSelected">
        <span>⭐</span> 我的选定
        <b v-if="selectedCount" class="sel-badge">{{ selectedCount }}</b>
        <span class="caret">{{ showSelected ? '▴' : '▾' }}</span>
      </button>

      <transition name="sel-slide">
        <div v-if="showSelected" class="selected-panel">
          <div class="sel-panel-head">
            <span class="sel-title">已选定 {{ selectedCount }} 件商品</span>
            <div class="sel-panel-actions">
              <button class="btn-ai-jump" @click="goBatch" :disabled="!selectedCount">
                🤖 AI 批量分析
              </button>
              <button class="btn-sel-export" @click="exportSelectedCSV" :disabled="!selectedCount">
                📥 导出选定
              </button>
              <button class="btn-sel-clear" @click="clearSelected" :disabled="!selectedCount">
                🗑 清空
              </button>
            </div>
          </div>

          <div v-if="selectedCount" class="sel-list">
            <div v-for="p in selectedList" :key="p.id" class="sel-item">
              <div class="sel-item-info">
                <div class="sel-item-name">{{ p.name }}</div>
                <div class="sel-item-meta">
                  <span class="cat">{{ p.category || '未分类' }}</span>
                  <span class="price">¥{{ p.price }}</span>
                  <span>📊 {{ formatNum(p.sales_volume) }}</span>
                  <span>⭐ {{ p.rating }}</span>
                  <span class="plat">{{ p.platform }}</span>
                </div>
              </div>
              <button class="sel-item-del" @click="removeSelected(p.id)" title="移除该商品">✕</button>
            </div>
          </div>

          <div v-else class="sel-empty">暂未选定商品，可在商品卡片点击「选定」加入</div>
        </div>
      </transition>
    </div>

    <!-- ② 搜索输入框 + 蓝色搜索按钮 -->
    <div class="search-box">
      <span class="search-ico">🔍</span>
      <input
        v-model="query"
        class="search-input"
        placeholder="输入商品关键词、品类、卖点..."
        @keyup.enter="doSearch"
      />
      <button class="btn-search" @click="doSearch" :disabled="loading">
        {{ loading ? '搜索中...' : '搜索' }}
      </button>
    </div>

    <!-- ③ 快捷搜索标签 -->
    <div class="quick-tags">
      <span class="tags-label">🔥 热门示例：</span>
      <button
        v-for="tag in quickTags"
        :key="tag"
        class="tag"
        :class="{ active: query === tag }"
        @click="useQuickTag(tag)"
      >{{ tag }}</button>
    </div>

    <!-- ④ 高级筛选行 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>价格区间</label>
        <div class="price-range">
          <span class="price-val">¥{{ priceMin }}</span>
          <input
            type="range"
            :min="priceRangeMin"
            :max="priceRangeMax"
            :step="1"
            v-model.number="priceMin"
            class="slider"
          />
          <input
            type="range"
            :min="priceRangeMin"
            :max="priceRangeMax"
            :step="1"
            v-model.number="priceMax"
            class="slider"
          />
          <span class="price-val">¥{{ priceMax }}</span>
        </div>
      </div>

      <div class="filter-item">
        <label>类目</label>
        <select v-model="selectedCategory" class="select">
          <option value="">全部类目</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div class="filter-item">
        <label>排序</label>
        <select v-model="selectedSort" class="select">
          <option value="relevance">匹配度从高到低</option>
          <option value="sales_desc">销量从高到低</option>
          <option value="rating_desc">评分从高到低</option>
          <option value="price_asc">价格从低到高</option>
          <option value="price_desc">价格从高到低</option>
          <option value="newest">最新上架</option>
        </select>
      </div>

      <button class="btn-reset" @click="resetFilters">重置</button>
    </div>

    <!-- ⑤ 主体区域 -->
    <div class="main-area">
      <!-- 未搜索：推荐潜力商品 -->
      <div v-if="!hasSearched" class="recommend-area">
        <h3 class="section-title">💡 系统推荐 · 潜力商品</h3>
        <div v-if="!recommendLoading && recommended.length" class="recommend-grid">
          <div
            v-for="item in recommended"
            :key="item.id"
            class="product-card recommend-card"
            @click="quickSearch(item.name)"
          >
            <div class="card-header">
              <span class="category-tag">{{ item.category }}</span>
              <span class="potential-badge">潜力 {{ item.potential_score }}</span>
            </div>
            <div class="card-name">{{ item.name }}</div>
            <div class="card-meta">
              <span class="price">¥{{ item.price }}</span>
              <span class="sales">📊 {{ formatNum(item.sales_volume) }}</span>
              <span class="rating">⭐ {{ item.rating }}</span>
            </div>
            <div class="card-desc">{{ item.description }}</div>
            <div class="card-foot">
              <button
                class="select-btn"
                :class="{ on: isSelected(item.id) }"
                @click.stop="toggleSelect(item)"
              >
                <span class="heart">{{ isSelected(item.id) ? '♥' : '♡' }}</span>{{ isSelected(item.id) ? '已选定' : '选定' }}
              </button>
            </div>
          </div>
        </div>
        <div v-if="recommendLoading" class="loading">加载推荐商品中...</div>
      </div>

      <!-- 已搜索：商品列表 -->
      <div v-else class="results-area">
        <div class="results-header">
          <h3 class="section-title">
            {{ isSemanticSearch ? '🔍 搜索结果' : '📋 商品列表' }}
            <span class="count">共 {{ total }} 条</span>
          </h3>
          <div class="results-actions">
            <button class="btn-export" @click="exportCSV" :disabled="!results.length">
              📥 导出 CSV
            </button>
          </div>
        </div>

        <div v-if="results.length" class="results-list">
          <div
            v-for="item in results"
            :key="isSemanticSearch ? item.product.id : item.id"
            class="product-card result-card"
          >
            <div v-if="isSemanticSearch" class="match-bar">
              <div
                class="match-fill"
                :style="{ width: (item.score * 100) + '%' }"
              ></div>
              <span class="match-text">{{ (item.score * 100).toFixed(0) }}%</span>
            </div>
            <div class="card-header">
              <span class="category-tag">{{ isSemanticSearch ? item.product.category : item.category }}</span>
              <span v-if="isSemanticSearch" class="score-tag">匹配度 {{ (item.score * 100).toFixed(0) }}%</span>
            </div>
            <div class="card-name">{{ isSemanticSearch ? item.product.name : item.name }}</div>
            <div class="card-meta">
              <span class="price">¥{{ isSemanticSearch ? item.product.price : item.price }}</span>
              <span class="sales">📊 {{ formatNum(isSemanticSearch ? item.product.sales_volume : item.sales_volume) }}</span>
              <span class="rating">⭐ {{ isSemanticSearch ? item.product.rating : item.rating }}</span>
              <span class="platform">{{ isSemanticSearch ? item.product.platform : item.platform }}</span>
            </div>
            <div class="card-desc">{{ (isSemanticSearch ? item.product.description : item.description) || (isSemanticSearch ? item.matched_chunk : '') }}</div>
            <div class="card-foot">
              <button
                class="select-btn"
                :class="{ on: isSelected(curProduct(item).id) }"
                @click.stop="toggleSelect(curProduct(item))"
              >
                <span class="heart">{{ isSelected(curProduct(item).id) ? '♥' : '♡' }}</span>{{ isSelected(curProduct(item).id) ? '已选定' : '选定' }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="!results.length && !loading" class="empty">
          <div class="empty-ico">🔍</div>
          <p>未找到相关商品</p>
          <button class="btn-retry" @click="resetFilters">重置筛选条件</button>
        </div>

        <!-- 分页 -->
        <div v-if="total > pageSize" class="pagination">
          <button class="page-btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useRouter } from 'vue-router'
import { selectedCount, selectedList, isSelected, toggleSelect, exportSelectedCSV, clearSelected, removeSelected } from '../selected'

// 取商品对象（兼容语义搜索 item.product 与浏览模式 item 两种结构）
function curProduct(item) {
  return isSemanticSearch.value ? item.product : item
}

// ---- 状态 ----
const query = ref('')
const results = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const hasSearched = ref(false)
const isSemanticSearch = ref(false)

// 筛选
const categories = ref([])
const selectedCategory = ref('')
const selectedSort = ref('relevance')
const priceRangeMin = ref(0)
const priceRangeMax = ref(1000)
const priceMin = ref(0)
const priceMax = ref(1000)

// 推荐
const recommended = ref([])
const recommendLoading = ref(false)
const initialized = ref(false)

// 选定面板展开状态（默认隐藏）
const showSelected = ref(false)

const router = useRouter()

// 跳转到 AI 对话页进行批量分析
function goBatch() {
  if (!selectedCount.value) return
  router.push('/chat?batch=1')
}

// 快捷标签（热门搜索词，确保语义搜索有好的演示效果）
const quickTags = computed(() => {
  return ['蓝牙耳机', '机械键盘', '智能手环', '面膜', '零食']
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ---- 工具 ----
function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toString()
}

// ---- 加载筛选配置 ----
async function loadFilters() {
  try {
    const res = await api.get('/api/products/filters')
    const data = await res.json()
    categories.value = data.categories
    priceRangeMin.value = Math.floor(data.price_min)
    priceRangeMax.value = Math.ceil(data.price_max)
    priceMin.value = priceRangeMin.value
    priceMax.value = priceRangeMax.value
  } catch (e) {
    console.error('加载筛选配置失败:', e)
  }
}

// ---- 加载推荐商品 ----
async function loadRecommended() {
  recommendLoading.value = true
  try {
    const res = await api.get('/api/products/recommended?limit=8')
    recommended.value = await res.json()
  } catch (e) {
    console.error('加载推荐失败:', e)
  } finally {
    recommendLoading.value = false
  }
}

// ---- 搜索 ----
async function doSearch() {
  // 价格夹取保护
  if (priceMin.value > priceMax.value) {
    [priceMin.value, priceMax.value] = [priceMax.value, priceMin.value]
    return // 交换后 watch 会自动重新触发
  }

  const q = query.value.trim()
  loading.value = true
  hasSearched.value = true

  try {
    if (q) {
      // 语义搜索模式
      isSemanticSearch.value = true
      const params = new URLSearchParams()
      if (selectedCategory.value) params.set('category', selectedCategory.value)
      if (priceMin.value > priceRangeMin.value) params.set('min_price', priceMin.value)
      if (priceMax.value < priceRangeMax.value) params.set('max_price', priceMax.value)
      params.set('sort_by', selectedSort.value)
      params.set('page', page.value)
      params.set('page_size', pageSize)

      const res = await api.post(`/api/search/?${params.toString()}`, {
        query: q,
        top_k: 50,
      })
      const data = await res.json()
      results.value = data.results
      total.value = data.total
    } else {
      // 纯浏览模式（无关键词）
      isSemanticSearch.value = false
      await loadProducts()
    }
  } catch (e) {
    console.error('搜索失败:', e)
  } finally {
    loading.value = false
  }
}

// ---- 加载商品列表（浏览模式） ----
async function loadProducts() {
  const params = new URLSearchParams()
  if (selectedCategory.value) params.set('category', selectedCategory.value)
  if (priceMin.value > priceRangeMin.value) params.set('min_price', priceMin.value)
  if (priceMax.value < priceRangeMax.value) params.set('max_price', priceMax.value)
  // 浏览模式没有匹配度，relevance 降级为 sales_desc
  const sortBy = selectedSort.value === 'relevance' ? 'sales_desc' : selectedSort.value
  params.set('sort_by', sortBy)
  params.set('page', page.value)
  params.set('page_size', pageSize)

  const res = await api.get(`/api/products/?${params.toString()}`)
  const data = await res.json()
  results.value = data.items
  total.value = data.total
}

// ---- 快捷标签 ----
function useQuickTag(tag) {
  query.value = tag
  page.value = 1
  doSearch()
}

// ---- 点击推荐卡片快速搜索 ----
function quickSearch(name) {
  query.value = name
  page.value = 1
  doSearch()
}

// ---- 重置筛选 ----
function resetFilters() {
  query.value = ''
  selectedCategory.value = ''
  selectedSort.value = 'relevance'
  priceMin.value = priceRangeMin.value
  priceMax.value = priceRangeMax.value
  page.value = 1
  hasSearched.value = false
  results.value = []
  total.value = 0
}

// ---- 分页 ----
function goPage(p) {
  page.value = p
  if (hasSearched.value) {
    doSearch()
  }
}

// ---- 导出 CSV ----
function exportCSV() {
  if (!results.value.length) return
  const headers = ['商品名称', '类目', '价格', '销量', '评分', '平台', '描述']
  const rows = results.value.map(item => {
    const p = isSemanticSearch.value ? item.product : item
    return [
      p.name,
      p.category || '',
      p.price || '',
      p.sales_volume || '',
      p.rating || '',
      p.platform || '',
      (p.description || '').replace(/[\r\n,]/g, ' '),
    ]
  })
  const csv = '\uFEFF' + [headers.join(','), ...rows.map(r => r.map(c => `"${c}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `商品列表_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// ---- 监听筛选变化自动搜索 ----
watch([priceMin, priceMax, selectedCategory, selectedSort], () => {
  if (!initialized.value) return // 初始化期间不触发
  page.value = 1
  if (hasSearched.value) {
    doSearch()
  } else {
    // 未搜索状态下改变筛选 → 自动进入浏览模式
    hasSearched.value = true
    doSearch()
  }
})

// ---- 初始化 ----
onMounted(async () => {
  await loadFilters()
  loadRecommended()
  initialized.value = true
})
</script>

<style scoped>
.page-header { margin-bottom: 22px; }
.page-header h2 {
  font-size: 22px; color: var(--text); margin: 0 0 6px; font-weight: 800;
  padding-left: 12px; border-left: 4px solid var(--primary);
}
.desc { color: var(--text-mute); font-size: 14px; margin: 0; padding-left: 16px; }

/* ---- 搜索框 ---- */
.search-box {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
  background: #fff;
  border-radius: var(--radius);
  padding: 6px 6px 6px 16px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: box-shadow .2s, border-color .2s;
}
.search-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(18,183,245,.12), var(--shadow);
}
.search-ico { font-size: 16px; opacity: .5; }
.search-input {
  flex: 1; padding: 12px 8px; border: none;
  font-size: 15px; outline: none; background: transparent; color: var(--text);
}
.search-input::placeholder { color: var(--text-mute); }
.btn-search {
  padding: 12px 34px; background: var(--primary-grad); color: #fff; border: none;
  border-radius: var(--radius-sm); font-size: 15px; cursor: pointer; white-space: nowrap; font-weight: 600;
  box-shadow: var(--shadow-primary);
  transition: transform .2s, box-shadow .2s;
}
.btn-search:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 28px rgba(18,183,245,.4); }
.btn-search:active:not(:disabled) { transform: translateY(0); }
.btn-search:disabled { opacity: .6; cursor: not-allowed; }

/* ---- 快捷标签 ---- */
.quick-tags {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 16px; padding: 12px 16px;
  background: var(--bg-soft); border: 1px solid var(--border);
  border-radius: var(--radius);
}
.tags-label { font-size: 13px; color: var(--text-sub); font-weight: 600; }
.tag {
  padding: 6px 14px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: 999px; font-size: 13px; color: var(--text-sub); cursor: pointer;
  transition: all .2s;
}
.tag:hover { border-color: var(--primary); color: var(--primary); background: var(--primary-50); }
.tag.active { background: var(--primary-grad); color: #fff; border-color: transparent; box-shadow: 0 4px 10px rgba(18,183,245,.3); }

/* ---- 筛选栏 ---- */
.filter-bar {
  display: flex; align-items: flex-end; gap: 22px; flex-wrap: wrap;
  padding: 18px 22px; background: #fff;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm); margin-bottom: 22px;
}
.filter-item { display: flex; flex-direction: column; gap: 6px; }
.filter-item label { font-size: 12px; color: var(--text-mute); font-weight: 600; letter-spacing: .3px; }
.select {
  padding: 9px 14px; border: 1px solid var(--border-strong); border-radius: var(--radius-sm);
  font-size: 14px; background: #fff; outline: none; min-width: 150px;
  cursor: pointer; color: var(--text);
  transition: border-color .2s, box-shadow .2s;
}
.select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(18,183,245,.12); }
.price-range {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-soft); padding: 8px 14px; border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.price-val { font-size: 13px; color: var(--primary); font-weight: 700; min-width: 50px; }
.slider { width: 100px; accent-color: var(--primary); }
.btn-reset {
  padding: 9px 20px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm); font-size: 13px; color: var(--text-sub); cursor: pointer;
  transition: all .2s; font-weight: 500;
}
.btn-reset:hover { border-color: var(--accent-red); color: var(--accent-red); background: #fff5f5; }

/* ---- 主体区域 ---- */
.main-area { min-height: 300px; }
.section-title {
  font-size: 16px; color: var(--text); margin: 0 0 18px;
  display: flex; align-items: center; gap: 12px; font-weight: 700;
  padding-left: 12px; border-left: 4px solid var(--primary);
}
.count { font-size: 13px; color: var(--text-mute); font-weight: normal; }

/* 推荐区 */
.recommend-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;
}
.recommend-card { cursor: pointer; transition: transform .2s, box-shadow .2s; }
.recommend-card:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); border-color: var(--primary); }
.potential-badge {
  background: linear-gradient(135deg, #ff9a56, #ff6b6b);
  color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 999px;
  font-weight: 600; box-shadow: 0 2px 6px rgba(255,107,107,.3);
}

/* 商品卡片 */
.product-card {
  background: #fff; border-radius: var(--radius); padding: 18px 20px;
  border: 1px solid var(--border); box-shadow: var(--shadow-sm);
  transition: transform .2s, box-shadow .2s, border-color .2s;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.category-tag {
  background: var(--primary-light); color: var(--primary-dark); font-size: 12px;
  padding: 3px 10px; border-radius: 999px; font-weight: 500;
}
.score-tag {
  color: var(--primary); font-size: 13px; font-weight: 700;
}
.card-name {
  font-size: 15px; font-weight: 600; color: var(--text);
  margin-bottom: 10px; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.card-meta {
  display: flex; gap: 14px; font-size: 13px; color: var(--text-sub); margin-bottom: 10px; flex-wrap: wrap;
}
.card-meta .price { color: var(--accent-red); font-weight: 700; font-size: 15px; }
.card-meta .platform { color: var(--text-mute); }
.card-desc {
  font-size: 13px; color: var(--text-mute); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

/* 匹配度条 */
.match-bar {
  position: relative; height: 6px; background: #eef1f6;
  border-radius: 999px; overflow: hidden; margin-bottom: 12px;
}
.match-fill {
  height: 100%; background: linear-gradient(90deg, var(--primary), #36C48F);
  border-radius: 999px; transition: width .3s;
}
.match-text {
  position: absolute; right: 6px; top: -3px; font-size: 10px;
  color: var(--primary-dark); font-weight: 700;
}

/* 结果区 */
.results-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px; flex-wrap: wrap; gap: 10px;
}
.results-header .section-title { margin-bottom: 0; }
.results-actions { display: flex; gap: 10px; }
.btn-export {
  padding: 9px 18px; background: var(--primary-50); border: 1px solid var(--primary);
  border-radius: var(--radius-sm); font-size: 13px; color: var(--primary-dark); cursor: pointer;
  font-weight: 600; transition: all .2s;
}
.btn-export:hover:not(:disabled) { background: var(--primary-grad); color: #fff; border-color: transparent; box-shadow: var(--shadow-primary); }
.btn-export:disabled { opacity: .5; cursor: not-allowed; }

.results-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;
}
.result-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); border-color: var(--primary); }

/* 分页 */
.pagination {
  display: flex; justify-content: center; align-items: center;
  gap: 16px; margin-top: 28px;
}
.page-btn {
  padding: 9px 20px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm); font-size: 13px; color: var(--text-sub); cursor: pointer;
  transition: all .2s; font-weight: 500;
}
.page-btn:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); background: var(--primary-50); }
.page-btn:disabled { opacity: .5; cursor: not-allowed; }
.page-info { font-size: 14px; color: var(--text-sub); font-weight: 700; }

/* 空状态 */
.empty { text-align: center; padding: 70px 20px; color: var(--text-mute); }
.empty-ico { font-size: 48px; opacity: .4; margin-bottom: 16px; }
.empty p { font-size: 15px; margin: 0 0 18px; }
.btn-retry {
  padding: 10px 26px; background: var(--primary-grad); color: #fff; border: none;
  border-radius: var(--radius-sm); font-size: 14px; cursor: pointer; font-weight: 600;
  box-shadow: var(--shadow-primary); transition: transform .2s;
}
.btn-retry:hover { transform: translateY(-1px); }

.loading { text-align: center; padding: 40px; color: var(--text-mute); }

/* 选定折叠按钮 + 展开面板 */
.selected-wrap { margin-bottom: 18px; }
.sel-toggle {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: 999px; font-size: 13px; color: var(--text-sub); cursor: pointer;
  transition: all .2s; font-weight: 500;
}
.sel-toggle:hover { border-color: #ffb300; color: #e65100; background: #fffdf5; }
.sel-toggle.has {
  border-color: #ffb300; color: #e65100;
  background: linear-gradient(135deg, #fff9e6, #fff4d6);
}
.sel-toggle .caret { font-size: 11px; opacity: .6; margin-left: 2px; }
.sel-badge {
  min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px;
  background: #e65100; color: #fff; font-size: 11px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
}

.selected-panel {
  margin-top: 10px;
  background: #fff; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden;
}
.sel-panel-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  padding: 12px 16px; background: var(--bg-soft); border-bottom: 1px solid var(--border);
}
.sel-title { font-size: 13px; color: var(--text); font-weight: 600; }
.sel-panel-actions { display: flex; gap: 8px; }
.btn-sel-export {
  padding: 6px 14px; background: #fff; border: 1px solid #ffb300;
  border-radius: 999px; font-size: 12px; color: #e65100; cursor: pointer;
  font-weight: 600; transition: all .2s;
}
.btn-sel-export:hover:not(:disabled) { background: #ffb300; color: #fff; }
.btn-sel-clear {
  padding: 6px 12px; background: #fff; border: 1px solid var(--border-strong);
  border-radius: 999px; font-size: 12px; color: var(--text-sub); cursor: pointer;
  transition: all .2s;
}
.btn-sel-clear:hover:not(:disabled) { border-color: var(--accent-red); color: var(--accent-red); }
.btn-sel-export:disabled, .btn-sel-clear:disabled { opacity: .5; cursor: not-allowed; }

.sel-list { max-height: 360px; overflow-y: auto; }
.sel-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-bottom: 1px solid var(--border);
  transition: background .15s;
}
.sel-item:last-child { border-bottom: none; }
.sel-item:hover { background: var(--bg-soft); }
.sel-item-info { flex: 1; min-width: 0; }
.sel-item-name {
  font-size: 14px; font-weight: 600; color: var(--text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  margin-bottom: 4px;
}
.sel-item-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-mute); flex-wrap: wrap; align-items: center; }
.sel-item-meta .cat { color: var(--primary-dark); background: var(--primary-light); padding: 1px 8px; border-radius: 999px; }
.sel-item-meta .price { color: var(--accent-red); font-weight: 700; }
.sel-item-meta .plat { color: var(--text-mute); }
.sel-item-del {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
  border: 1px solid var(--border-strong); background: #fff;
  color: var(--text-mute); cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.sel-item-del:hover { background: var(--accent-red); border-color: var(--accent-red); color: #fff; transform: rotate(90deg); }

.sel-empty { text-align: center; padding: 32px 16px; color: var(--text-mute); font-size: 13px; }

/* 面板展开过渡 */
.sel-slide-enter-active, .sel-slide-leave-active { transition: all .25s ease; overflow: hidden; }
.sel-slide-enter-from, .sel-slide-leave-to { opacity: 0; max-height: 0; margin-top: 0; }
.sel-slide-enter-to, .sel-slide-leave-from { opacity: 1; max-height: 600px; }

/* 卡片选定按钮 */
.card-foot {
  display: flex; justify-content: flex-end;
  margin-top: 12px; padding-top: 10px;
  border-top: 1px dashed var(--border);
}
.select-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 14px; border-radius: 999px;
  border: 1px solid var(--border-strong); background: #fff;
  font-size: 12px; color: var(--text-sub); cursor: pointer;
  transition: all .2s; user-select: none;
}
.select-btn .heart { font-size: 14px; }
.select-btn:hover { border-color: var(--accent-red); color: var(--accent-red); }
.select-btn.on {
  background: #fff0f0; border-color: var(--accent-red); color: var(--accent-red); font-weight: 600;
}

/* AI 批量分析跳转按钮 */
.btn-ai-jump {
  padding: 6px 14px; border-radius: 999px; cursor: pointer; font-size: 12px; font-weight: 600;
  background: var(--primary-grad); border: none; color: #fff; transition: all .2s;
  box-shadow: var(--shadow-primary);
}
.btn-ai-jump:hover:not(:disabled) { transform: translateY(-1px); }
.btn-ai-jump:disabled { opacity: .5; cursor: not-allowed; }

/* 响应式 */
@media (max-width: 768px) {
  .results-list { grid-template-columns: 1fr; }
  .recommend-grid { grid-template-columns: 1fr; }
  .filter-bar { flex-direction: column; align-items: stretch; }
  .slider { width: 80px; }
  .search-box { padding: 6px 6px 6px 12px; }
  .btn-search { padding: 12px 22px; }
}
</style>

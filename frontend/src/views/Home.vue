<template>
  <div class="home">
    <!-- Hero 横幅 -->
    <section class="hero">
      <div class="hero-glow"></div>
      <div class="hero-content">
        <h2>欢迎使用 AI 电商选品助手</h2>
        <p>智能商品语义检索 + AI 选品分析，基于 RAG 技术让数据驱动决策</p>
        <div class="hero-tags">
          <span class="htag">🔍 语义检索</span>
          <span class="htag">📊 数据看板</span>
          <span class="htag">🤖 AI 分析</span>
        </div>
      </div>
    </section>

    <!-- 功能入口卡 -->
    <div class="cards">
      <router-link to="/search" class="card card-blue">
        <span class="icon">🔍</span>
        <h3>商品检索</h3>
        <p>自然语言搜索商品，语义匹配更精准，结果按相关度排序</p>
        <span class="card-cta">立即检索 →</span>
      </router-link>

      <router-link to="/chat" class="card card-purple">
        <span class="icon">💬</span>
        <h3>AI 选品分析</h3>
        <p>基于真实商品数据，AI 给出有数据支撑的选品建议和趋势分析</p>
        <span class="card-cta">开始对话 →</span>
      </router-link>
    </div>

    <!-- 数据看板 -->
    <div class="dashboard">
      <div class="dashboard-header">
        <h3>📊 商品数据看板</h3>
        <button class="btn-refresh" @click="loadStats" :disabled="loading">
          {{ loading ? '加载中...' : '↻ 刷新' }}
        </button>
      </div>

      <!-- 指标卡 -->
      <div class="metric-cards">
        <div class="metric-card" v-for="m in metricCards" :key="m.key">
          <div class="metric-icon" :style="{ background: m.bg }">{{ m.icon }}</div>
          <div class="metric-info">
            <div class="metric-value">{{ m.value }}</div>
            <div class="metric-label">{{ m.label }}</div>
          </div>
        </div>
      </div>

      <!-- 图表区 -->
      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-title">类目分布</div>
          <div ref="pieRef" class="chart-box"></div>
        </div>
        <div class="chart-card">
          <div class="chart-title">价格区间分布</div>
          <div ref="barRef" class="chart-box"></div>
        </div>
        <div class="chart-card chart-wide">
          <div class="chart-title">平台销量对比</div>
          <div ref="lineRef" class="chart-box"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated, nextTick, computed, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { api } from '../api'

const loading = ref(false)
const stats = ref(null)
const pieRef = ref(null)
const barRef = ref(null)
const lineRef = ref(null)
let pieChart = null, barChart = null, lineChart = null

const metricCards = computed(() => {
  const s = stats.value?.summary
  return [
    { key: 'total', icon: '📦', label: '商品总数', value: s?.total_products ?? '-', bg: 'linear-gradient(135deg, #12B7F5, #0D8BD9)' },
    { key: 'category', icon: '🏷', label: '类目数量', value: s?.category_count ?? '-', bg: 'linear-gradient(135deg, #9B6BFF, #7B4EE8)' },
    { key: 'hot', icon: '🔥', label: '热销商品', value: s?.hot_products ?? '-', bg: 'linear-gradient(135deg, #FF7E3D, #F55E2C)' },
    { key: 'alert', icon: '⚠️', label: '库存预警', value: s?.stock_alerts ?? '-', bg: 'linear-gradient(135deg, #FFB23D, #F5951E)' },
  ]
})

async function loadStats() {
  loading.value = true
  try {
    const res = await api.get('/api/products/stats')
    if (res.ok) {
      stats.value = await res.json()
      await nextTick()
      renderCharts()
    }
  } catch (e) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  const data = stats.value
  if (!data) return

  // 销毁旧实例
  pieChart?.dispose()
  barChart?.dispose()
  lineChart?.dispose()

  // 饼图 - 类目分布
  pieChart = echarts.init(pieRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, left: 'center', itemWidth: 10, itemHeight: 10, itemGap: 8, textStyle: { fontSize: 11 } },
    color: ['#12B7F5', '#9B6BFF', '#FF7E3D', '#36C48F', '#FF5C8A', '#FFB23D', '#3DAEFF', '#5BCE65', '#7B4EE8', '#F55E2C'],
    series: [{
      type: 'pie',
      center: ['50%', '44%'],
      radius: ['35%', '62%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: data.category_distribution,
    }],
  })

  // 柱状图 - 价格区间
  barChart = echarts.init(barRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.price_distribution.map(d => d.name), axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: data.price_distribution.map(d => d.value),
      barWidth: '50%',
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#12B7F5' },
          { offset: 1, color: '#0D8BD9' },
        ]),
      },
    }],
  })

  // 横向条形图 - 平台销量对比
  lineChart = echarts.init(lineRef.value)
  const platformData = data.platform_sales || []
  lineChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = platformData[params[0].dataIndex]
        return `${p.name}<br/>总销量: ${p.sales.toLocaleString()}<br/>商品数: ${p.count}`
      },
    },
    grid: { left: 80, right: 60, top: 20, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 }, splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: {
      type: 'category',
      data: platformData.map(d => d.name),
      axisLabel: { fontSize: 13, fontWeight: 'bold' },
    },
    series: [{
      type: 'bar',
      data: platformData.map(d => d.sales),
      barWidth: '50%',
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: (params) => {
          const colors = ['#FF6B6B', '#FF9A56', '#12B7F5', '#36C48F', '#9B6BFF']
          return colors[params.dataIndex % colors.length]
        },
      },
      label: {
        show: true,
        position: 'right',
        formatter: (params) => {
          const v = params.value
          return v >= 10000 ? (v / 10000).toFixed(1) + 'w' : v.toString()
        },
        fontSize: 12,
        color: '#666',
        fontWeight: 600,
      },
    }],
  })
}

function handleResize() {
  pieChart?.resize()
  barChart?.resize()
  lineChart?.resize()
}

let skipFirstActivate = true
onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})
onActivated(() => {
  // keep-alive 切回首页时刷新看板（跳过首次，onMounted 已加载）
  if (skipFirstActivate) { skipFirstActivate = false; return }
  loadStats()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  barChart?.dispose()
  lineChart?.dispose()
})
</script>

<style scoped>
.home { padding-bottom: 8px; }

/* Hero */
.hero {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl);
  padding: 44px 32px;
  background: linear-gradient(120deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%);
  color: #fff;
  text-align: center;
  margin-bottom: 32px;
  box-shadow: var(--shadow-lg);
}
.hero-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 15% 130%, rgba(18,183,245,.35), transparent 50%),
    radial-gradient(circle at 90% -30%, rgba(155,107,255,.25), transparent 45%);
  pointer-events: none;
}
.hero-content { position: relative; z-index: 1; }
.hero h2 {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 1px;
  text-shadow: 0 2px 16px rgba(0,0,0,.25);
}
.hero p {
  color: #b9c4dc;
  font-size: 14px;
  margin: 10px 0 22px;
  letter-spacing: .5px;
}
.hero-tags { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.htag {
  padding: 6px 16px;
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 999px;
  font-size: 12.5px;
  color: #d8e3f5;
  backdrop-filter: blur(4px);
}

/* 功能卡 */
.cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 36px;
}
.card {
  position: relative;
  background: var(--card);
  border-radius: var(--radius-lg);
  padding: 30px 26px;
  text-decoration: none;
  color: var(--text);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  overflow: hidden;
  transition: transform .25s cubic-bezier(.16,1,.3,1), box-shadow .25s;
}
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--primary-grad);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .3s ease;
}
.card.card-purple::before { background: linear-gradient(135deg, #9B6BFF, #7B4EE8); }
.card:hover { transform: translateY(-6px); box-shadow: var(--shadow-lg); }
.card:hover::before { transform: scaleX(1); }
.card .icon {
  font-size: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px; height: 64px;
  border-radius: var(--radius);
  background: var(--primary-light);
  margin-bottom: 16px;
}
.card.card-purple .icon { background: #f3ecff; }
.card h3 { font-size: 18px; margin-bottom: 8px; color: var(--text); }
.card p { font-size: 13px; color: var(--text-sub); line-height: 1.7; margin-bottom: 16px; }
.card-cta { font-size: 13px; font-weight: 600; color: var(--primary); }
.card.card-purple .card-cta { color: #7B4EE8; }

/* 数据看板 */
.dashboard { text-align: left; }
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.dashboard-header h3 {
  font-size: 18px;
  color: var(--text);
  padding-left: 12px;
  border-left: 4px solid var(--primary);
  font-weight: 700;
}
.btn-refresh {
  padding: 7px 16px;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-sub);
  cursor: pointer;
  transition: all .2s;
}
.btn-refresh:hover:not(:disabled) { background: var(--primary-50); border-color: var(--primary); color: var(--primary); }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

/* 指标卡 */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--shadow-sm);
  transition: transform .2s, box-shadow .2s;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); }
.metric-icon {
  width: 46px; height: 46px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,.12);
}
.metric-value { font-size: 24px; font-weight: 800; color: var(--text); line-height: 1.2; }
.metric-label { font-size: 12px; color: var(--text-mute); margin-top: 2px; }

/* 图表网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.chart-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow-sm);
}
.chart-card.chart-wide { grid-column: span 2; }
.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid var(--primary);
}
.chart-box { width: 100%; height: 260px; }

@media (max-width: 640px) {
  .cards { grid-template-columns: 1fr; }
  .metric-cards { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
  .chart-card.chart-wide { grid-column: span 1; }
  .hero { padding: 32px 20px; }
  .hero h2 { font-size: 22px; }
}
</style>

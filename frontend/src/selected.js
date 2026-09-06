import { reactive, computed } from 'vue'

const STORAGE_KEY = 'selected_products'

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch (e) {
    return {}
  }
}

function save(map) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch (e) {
    console.error('保存选定商品失败:', e)
  }
}

// 选定商品 map：{ [id]: { id, name, category, price, sales_volume, rating, platform, description, selectedAt } }
export const selectedState = reactive({
  items: load(),
})

// 已选定数量
export const selectedCount = computed(() => Object.keys(selectedState.items).length)

// 已选定列表（按选定时间升序）
export const selectedList = computed(() =>
  Object.values(selectedState.items).sort((a, b) => a.selectedAt - b.selectedAt)
)

// 判断某商品是否已选定
export function isSelected(id) {
  if (id == null) return false
  return !!selectedState.items[id]
}

// 切换选定/取消
export function toggleSelect(product) {
  if (!product || product.id == null) return
  const id = product.id
  if (selectedState.items[id]) {
    delete selectedState.items[id]
  } else {
    selectedState.items[id] = {
      id: product.id,
      name: product.name,
      category: product.category || '',
      price: product.price,
      sales_volume: product.sales_volume,
      rating: product.rating,
      platform: product.platform || '',
      description: (product.description || '').replace(/[\r\n,]/g, ' '),
      selectedAt: Date.now(),
    }
  }
  save(selectedState.items)
}

// 清空所有选定
export function clearSelected() {
  for (const k of Object.keys(selectedState.items)) {
    delete selectedState.items[k]
  }
  save(selectedState.items)
}

// 移除单条选定
export function removeSelected(id) {
  if (id == null) return
  delete selectedState.items[id]
  save(selectedState.items)
}

// 一键导出所有选定商品为 CSV
export function exportSelectedCSV() {
  const list = selectedList.value
  if (!list.length) return false
  const headers = ['商品名称', '类目', '价格', '销量', '评分', '平台', '描述']
  const rows = list.map(p => [
    p.name,
    p.category,
    p.price,
    p.sales_volume,
    p.rating,
    p.platform,
    p.description,
  ])
  const csv = '\uFEFF' + [headers.join(','), ...rows.map(r => r.map(c => `"${c}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `选定商品_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  return true
}

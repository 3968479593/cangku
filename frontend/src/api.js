import { authState, adminState, clearAuth, clearAdminAuth } from './auth'

// 判断是否为管理端请求（/api/admin 或 /api/documents）
function isAdminUrl(url) {
  return url.startsWith('/api/admin/') || url.startsWith('/api/documents')
}

// 是否处于管理员会话（仅有 admin token，无 user token）
function isAdminSession() {
  return !authState.token && !!adminState.token
}

// 根据请求 URL + 当前会话身份选择对应 token
function withAuth(headers = {}, url = '') {
  if (isAdminUrl(url)) {
    if (adminState.token) headers['Authorization'] = `Bearer ${adminState.token}`
  } else {
    // 非管理端 URL：优先 user token；管理员会话则用 admin token（后端 get_current_user 支持 admin）
    const token = authState.token || adminState.token
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

// 401 处理：按当前会话身份清理并跳转
function handle401(res, url) {
  if (res.status !== 401) return res
  // 登录/注册接口返回 401 是业务错误（密码错/账号不存在），交给调用方处理
  if (url.startsWith('/api/auth/') || url.startsWith('/api/admin/login')) {
    return res
  }
  if (isAdminUrl(url) || isAdminSession()) {
    clearAdminAuth()
    if (location.pathname !== '/admin/login') location.href = '/admin/login'
    throw new Error('管理员登录已过期')
  }
  clearAuth()
  if (location.pathname !== '/login') location.href = '/login'
  throw new Error('登录已过期')
}

export const api = {
  get(url) {
    return fetch(url, { headers: withAuth({}, url) }).then(res => handle401(res, url))
  },
  post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: withAuth({ 'Content-Type': 'application/json' }, url),
      body: JSON.stringify(body),
    }).then(res => handle401(res, url))
  },
  // 上传文件用 FormData，不预设 Content-Type（浏览器自动加 boundary）
  upload(url, formData) {
    return fetch(url, {
      method: 'POST',
      headers: withAuth({}, url),
      body: formData,
    }).then(res => handle401(res, url))
  },
  del(url) {
    return fetch(url, { method: 'DELETE', headers: withAuth({}, url) }).then(res => handle401(res, url))
  },
}

// 供流式请求（SSE）使用：只返回带认证头的 fetch，不自动处理 401
export function authFetch(url, options = {}) {
  return fetch(url, { ...options, headers: withAuth(options.headers, url) })
}

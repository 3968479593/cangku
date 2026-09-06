import { reactive } from 'vue'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'
const ADMIN_TOKEN_KEY = 'admin_token'
const ADMIN_KEY = 'admin_info'

// 全局登录态：token + 用户信息，同步到 localStorage
export const authState = reactive({
  token: localStorage.getItem(TOKEN_KEY) || '',
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
})

// 管理员登录态（独立存储，与普通用户互不干扰）
export const adminState = reactive({
  token: localStorage.getItem(ADMIN_TOKEN_KEY) || '',
  admin: JSON.parse(localStorage.getItem(ADMIN_KEY) || 'null'),
})

export function setAuth(token, user) {
  authState.token = token
  authState.user = user
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  authState.token = ''
  authState.user = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function setAdminAuth(token, admin) {
  adminState.token = token
  adminState.admin = admin
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
  localStorage.setItem(ADMIN_KEY, JSON.stringify(admin))
}

export function clearAdminAuth() {
  adminState.token = ''
  adminState.admin = null
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_KEY)
}

export function isLoggedIn() {
  return !!authState.token
}

export function isAdminLoggedIn() {
  return !!adminState.token
}

// 根据 username 生成稳定的渐变头像配色（QQ 风格彩色头像）
const AVATAR_COLORS = [
  ['#12B7F5', '#0D8BD9'],
  ['#FF7E3D', '#F55E2C'],
  ['#36C48F', '#1FA370'],
  ['#9B6BFF', '#7B4EE8'],
  ['#FF5C8A', '#E83A68'],
  ['#FFB23D', '#F5951E'],
  ['#3DAEFF', '#1E8FE0'],
  ['#5BCE65', '#3DAB47'],
]
export function avatarColors(username = '') {
  let h = 0
  for (let i = 0; i < username.length; i++) h = (h * 31 + username.charCodeAt(i)) >>> 0
  return AVATAR_COLORS[h % AVATAR_COLORS.length]
}

export function avatarText(nickname = '') {
  return (nickname.trim()[0] || '?').toUpperCase()
}

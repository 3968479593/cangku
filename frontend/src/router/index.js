import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isAdminLoggedIn } from '../auth'

const routes = [
  // 用户端（管理员也可访问）
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/search', name: 'Search', component: () => import('../views/Search.vue') },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue') },

  // 管理员专属功能页（嵌入主界面导航，复用用户布局）
  { path: '/docs', name: 'ManageDocs', component: () => import('../views/ManageDocs.vue'), meta: { admin: true } },
  { path: '/feedback', name: 'ManageFeedback', component: () => import('../views/ManageFeedback.vue'), meta: { admin: true } },

  // 管理员登录（独立布局，不套用户导航）
  { path: '/admin/login', name: 'AdminLogin', component: () => import('../views/AdminLogin.vue'), meta: { public: true, admin: true, layout: 'admin' } },
  // 管理员主界面即用户主界面（统一布局，导航多文档管理/用户反馈两个 tab）
  { path: '/admin', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to) => {
  if (to.meta.public) return true
  // 管理员专属路由必须用管理员登录态
  if (to.meta.admin) {
    if (!isAdminLoggedIn()) return { name: 'AdminLogin' }
    return true
  }
  // 用户端路由：用户或管理员登录态均可
  if (!isLoggedIn() && !isAdminLoggedIn()) return { name: 'Login' }
  return true
})

export default router

<template>
  <!-- 管理端独立布局：不套用户导航 -->
  <template v-if="isAdminLayout">
    <router-view />
  </template>

  <!-- 用户端布局 -->
  <div v-else class="app">
    <header class="header">
      <div class="header-inner">
        <span class="brand-logo">🛍</span>
        <div class="brand-text">
          <h1>AI 电商选品助手</h1>
          <span class="subtitle">智能商品检索 · 趋势分析</span>
        </div>
      </div>
    </header>

    <nav class="topnav">
      <div class="topnav-inner">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <span class="nav-ico">🏠</span>首页
        </router-link>
        <router-link to="/search" class="nav-item" active-class="active">
          <span class="nav-ico">🔍</span>商品检索
        </router-link>
        <router-link to="/chat" class="nav-item" active-class="active">
          <span class="nav-ico">💬</span>AI 对话
        </router-link>
        <router-link to="/docs" class="nav-item" active-class="active" v-if="isAdmin">
          <span class="nav-ico">📄</span>文档管理
        </router-link>
        <router-link to="/feedback" class="nav-item" active-class="active" v-if="isAdmin">
          <span class="nav-ico">💌</span>用户反馈
        </router-link>
        <div class="nav-right">
          <AdminBox v-if="isAdmin && showUserBox" />
          <UserBox v-else-if="showUserBox" />
        </div>
      </div>
    </nav>

    <main class="main">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>

    <footer class="footer">
      <span>AI 电商选品助手 · 数据驱动选品决策</span>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { adminState } from './auth'
import UserBox from './components/UserBox.vue'
import AdminBox from './components/AdminBox.vue'

const route = useRoute()
// admin 路由用独立布局（meta.layout === 'admin'），登录页不显示用户信息框
const isAdminLayout = computed(() => route.meta.layout === 'admin')
const isAdmin = computed(() => !!adminState.token)
const showUserBox = computed(() => route.name !== 'Login' && route.name !== 'AdminLogin')
</script>

<style>
/* ===== 全局设计系统 ===== */
:root {
  --primary: #12B7F5;
  --primary-dark: #0D8BD9;
  --primary-darker: #0A6FB8;
  --primary-light: #e6f7ff;
  --primary-50: #f0f9ff;

  --accent-purple: #9B6BFF;
  --accent-orange: #FF7E3D;
  --accent-green: #36C48F;
  --accent-red: #ff4d4f;

  --bg: #f4f7fb;
  --bg-soft: #f8fafd;
  --text: #1a2233;
  --text-sub: #5b6478;
  --text-mute: #9aa3b2;
  --card: #ffffff;
  --border: #e9edf3;
  --border-strong: #dde3ec;

  --radius-sm: 8px;
  --radius: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;

  --shadow-sm: 0 1px 3px rgba(16,27,51,.05);
  --shadow: 0 4px 18px rgba(16,27,51,.07);
  --shadow-lg: 0 14px 44px rgba(16,27,51,.13);
  --shadow-primary: 0 8px 24px rgba(18,183,245,.28);

  --header-grad: linear-gradient(120deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%);
  --primary-grad: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 100%);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; }
body {
  font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}

/* ===== 顶栏 ===== */
.header {
  background: var(--header-grad);
  color: #fff;
  padding: 22px 0;
  position: relative;
  overflow: hidden;
}
.header::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 120%, rgba(18,183,245,.28), transparent 45%),
    radial-gradient(circle at 88% -20%, rgba(155,107,255,.20), transparent 40%);
  pointer-events: none;
}
.header-inner {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.brand-logo {
  font-size: 34px;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.25));
  animation: float-y 3s ease-in-out infinite;
}
@keyframes float-y {
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.brand-text { text-align: center; }
.header h1 {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 1px;
  text-shadow: 0 2px 12px rgba(0,0,0,.2);
}
.subtitle {
  font-size: 13px;
  color: #9aa8c4;
  display: block;
  margin-top: 4px;
  letter-spacing: 1px;
}

/* ===== 导航 ===== */
.topnav {
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: center;
  position: sticky;
  top: 0;
  z-index: 50;
  box-shadow: 0 2px 12px rgba(16,27,51,.04);
}
.topnav-inner {
  display: flex;
  gap: 6px;
  align-items: center;
  width: 100%;
  max-width: 1080px;
  padding: 8px 16px;
}
.nav-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  text-decoration: none;
  color: var(--text-sub);
  font-size: 14px;
  font-weight: 500;
  border-radius: 999px;
  transition: all .2s ease;
}
.nav-ico { font-size: 15px; }
.nav-item:hover {
  color: var(--primary);
  background: var(--primary-50);
}
.nav-item.active {
  color: #fff;
  background: var(--primary-grad);
  box-shadow: 0 4px 12px rgba(18,183,245,.32);
  font-weight: 600;
}
.nav-right { margin-left: auto; padding: 0 4px; }

.main {
  max-width: 1080px;
  margin: 0 auto;
  padding: 36px 24px 48px;
}

/* 页脚 */
.footer {
  text-align: center;
  padding: 24px 16px 32px;
  color: var(--text-mute);
  font-size: 12px;
  letter-spacing: .5px;
}

/* 全局滚动条美化 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #cfd6e0; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #b3bcc9; }
::-webkit-scrollbar-track { background: transparent; }

@media (max-width: 640px) {
  .header-inner { justify-content: center; }
  .nav-item { padding: 8px 14px; font-size: 13px; }
  .main { padding: 24px 16px 40px; }
}
</style>

<template>
  <div class="admin-login-page">
    <div class="bg-pattern"></div>
    <div class="bg-blob blob1"></div>
    <div class="bg-blob blob2"></div>
    <div class="bg-blob blob3"></div>
    <div class="login-card">
      <div class="card-header">
        <div class="logo">🛡</div>
        <h2>管理后台</h2>
        <p>AI 电商选品助手 · 管理员入口</p>
      </div>

      <div class="field">
        <span class="icon">👤</span>
        <input v-model="form.username" type="text" placeholder="请输入管理员账号" @keyup.enter="onLogin" />
      </div>

      <div class="field">
        <span class="icon">🔒</span>
        <input
          v-model="form.password"
          :type="showPwd ? 'text' : 'password'"
          placeholder="请输入密码"
          @keyup.enter="onLogin"
        />
        <span class="eye" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁' }}</span>
      </div>

      <transition name="msg-fade">
        <div v-if="msg" class="msg err">
          <span class="msg-icon">✕</span>
          {{ msg }}
        </div>
      </transition>

      <button class="btn-submit" :disabled="loading" @click="onLogin">
        {{ loading ? '登录中...' : '管理员登录' }}
      </button>

      <div class="back-link">
        <a href="/login">← 返回用户登录</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { setAdminAuth } from '../auth'

const router = useRouter()
const showPwd = ref(false)
const loading = ref(false)
const msg = ref('')
const form = reactive({ username: '', password: '' })

async function onLogin() {
  msg.value = ''
  if (!form.username || !form.password) {
    msg.value = '账号和密码不能为空'
    return
  }

  loading.value = true
  try {
    const res = await api.post('/api/admin/login', {
      username: form.username,
      password: form.password,
    })
    const data = await res.json()
    if (!res.ok) {
      msg.value = data.detail || '登录失败'
      return
    }
    setAdminAuth(data.access_token, data.admin)
    setTimeout(() => router.push('/'), 400)
  } catch (e) {
    msg.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 20% 20%, rgba(18,183,245,.15), transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(155,107,255,.12), transparent 50%),
    linear-gradient(135deg, #0f1729 0%, #16213e 45%, #0f3460 100%);
  padding: 140px 20px;
  overflow: hidden;
}
.bg-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 40px 40px;
  z-index: 0;
  -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 75%);
  mask-image: radial-gradient(circle at center, black 30%, transparent 75%);
}
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: .55;
  z-index: 0;
  animation: float 14s ease-in-out infinite;
}
.blob1 { width: 340px; height: 340px; background: rgba(18,183,245,.40); top: -70px; left: -50px; }
.blob2 { width: 300px; height: 300px; background: rgba(155,107,255,.35); bottom: -60px; right: -40px; animation-delay: -5s; }
.blob3 { width: 220px; height: 220px; background: rgba(54,196,143,.25); top: 45%; left: 55%; animation-delay: -9s; }
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(35px, -25px) scale(1.1); }
  66% { transform: translate(-25px, 30px) scale(.92); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 40px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .5);
  animation: card-in 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes card-in {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.card-header {
  text-align: center;
  margin-bottom: 28px;
}
.logo {
  font-size: 48px;
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 12px rgba(18, 183, 245, 0.5));
}
.card-header h2 {
  font-size: 22px;
  color: #fff;
  font-weight: 700;
  margin-bottom: 6px;
  letter-spacing: 2px;
}
.card-header p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.field {
  display: flex;
  align-items: center;
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  padding: 0 14px;
  margin-bottom: 16px;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.04);
}
.field:focus-within {
  border-color: #12B7F5;
  background: rgba(18, 183, 245, 0.08);
  box-shadow: 0 0 0 4px rgba(18, 183, 245, 0.15);
}
.field .icon { font-size: 15px; opacity: .5; }
.field input {
  flex: 1;
  border: none;
  outline: none;
  padding: 12px 10px;
  font-size: 14px;
  background: transparent;
  color: #fff;
}
.field input::placeholder { color: rgba(255, 255, 255, 0.4); }
.field .eye {
  cursor: pointer;
  font-size: 16px;
  opacity: .5;
  user-select: none;
  transition: opacity .2s, transform .2s;
  padding: 0 4px;
}
.field .eye:hover { opacity: 1; transform: scale(1.15); }

.msg {
  font-size: 13px;
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 8px;
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
  background: #f44336;
  color: #fff;
}
.msg.err {
  color: #ffb4b4;
  background: rgba(244, 67, 54, 0.15);
  border: 1px solid rgba(244, 67, 54, 0.3);
}
.msg-fade-enter-active, .msg-fade-leave-active { transition: all 0.3s ease; }
.msg-fade-enter-from, .msg-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.btn-submit {
  width: 100%;
  padding: 13px;
  background: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-top: 6px;
  letter-spacing: 2px;
  box-shadow: 0 4px 14px rgba(18, 183, 245, 0.35);
}
.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(18, 183, 245, 0.5);
}
.btn-submit:active { transform: translateY(0); }
.btn-submit:disabled {
  opacity: .6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.back-link {
  text-align: center;
  margin-top: 22px;
}
.back-link a {
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 13px;
  transition: color .2s;
}
.back-link a:hover { color: #12B7F5; }

@media (max-width: 480px) {
  .login-card { width: 320px; padding: 32px 24px; }
}
</style>

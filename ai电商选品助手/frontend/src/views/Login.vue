<template>
  <div class="login-page">
    <!-- 动态背景气泡 -->
    <div class="bg-bubbles">
      <span class="bubble b1"></span>
      <span class="bubble b2"></span>
      <span class="bubble b3"></span>
      <span class="bubble b4"></span>
      <span class="bubble b5"></span>
      <span class="bubble b6"></span>
    </div>

    <div class="login-card">
      <!-- 左侧品牌区（QQ 风格） -->
      <div class="brand-side">
        <div class="brand-logo">🛍</div>
        <h2>AI 电商选品助手</h2>
        <p>智能商品检索 · 趋势分析</p>
        <div class="brand-features">
          <div class="feat"><span>✓</span> 智能选品推荐</div>
          <div class="feat"><span>✓</span> 实时趋势分析</div>
          <div class="feat"><span>✓</span> 一键商品检索</div>
        </div>
        <p class="brand-sub">登录后开启选品之旅</p>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-side">
        <div class="form-header">
          <div class="avatar">👤</div>
          <h3>{{ isRegister ? '创建账号' : '欢迎回来' }}</h3>
          <p class="form-tip">{{ isRegister ? '填写信息完成注册' : '请登录您的账号' }}</p>
        </div>

        <div class="field">
          <span class="icon">👤</span>
          <input v-model="form.username" type="text" placeholder="请输入账号" @keyup.enter="onSubmit" />
        </div>

        <div class="field" v-if="isRegister">
          <span class="icon">😊</span>
          <input v-model="form.nickname" type="text" placeholder="请输入昵称" @keyup.enter="onSubmit" />
        </div>

        <div class="field">
          <span class="icon">🔒</span>
          <input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="请输入密码"
            @keyup.enter="onSubmit"
          />
          <span class="eye" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁' }}</span>
        </div>

        <div class="field" v-if="isRegister">
          <span class="icon">🔒</span>
          <input
            v-model="form.confirm"
            :type="showPwd ? 'text' : 'password'"
            placeholder="请再次输入密码"
            @keyup.enter="onSubmit"
          />
          <span class="eye" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁' }}</span>
        </div>

        <transition name="msg-fade">
          <div v-if="msg" :class="['msg', msgOk ? 'ok' : 'err']">
            <span class="msg-icon">{{ msgOk ? '✓' : '✕' }}</span>
            {{ msg }}
          </div>
        </transition>

        <button class="btn-submit" :disabled="loading" @click="onSubmit">
          <span class="btn-text">{{ loading ? '处理中...' : (isRegister ? '注 册' : '登 录') }}</span>
        </button>

        <div class="switch-mode">
          <span v-if="!isRegister">还没有账号？</span>
          <span v-else>已有账号？</span>
          <a href="javascript:;" @click="toggleMode">{{ isRegister ? '去登录' : '注册新账号' }}</a>
        </div>

        <div class="admin-entry">
          <a href="/admin/login">🛡 管理员入口</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { setAuth } from '../auth'

const router = useRouter()
const isRegister = ref(false)
const showPwd = ref(false)
const loading = ref(false)
const msg = ref('')
const msgOk = ref(false)

const form = reactive({ username: '', nickname: '', password: '', confirm: '' })

function toggleMode() {
  isRegister.value = !isRegister.value
  msg.value = ''
  form.confirm = ''
}

async function onSubmit() {
  msg.value = ''
  if (!form.username || !form.password) {
    msg.value = '账号和密码不能为空'
    return
  }
  if (isRegister.value) {
    if (!form.nickname) { msg.value = '请填写昵称'; return }
    if (form.password.length < 6) { msg.value = '密码至少 6 位'; return }
    if (form.password !== form.confirm) { msg.value = '两次密码不一致'; return }
  }

  loading.value = true
  try {
    const url = isRegister.value ? '/api/auth/register' : '/api/auth/login'
    const body = isRegister.value
      ? { username: form.username, password: form.password, nickname: form.nickname }
      : { username: form.username, password: form.password }
    const res = await api.post(url, body)
    const data = await res.json()
    if (!res.ok) {
      msg.value = data.detail || '操作失败'
      return
    }
    setAuth(data.access_token, data.user)
    msgOk.value = true
    msg.value = isRegister.value ? '注册成功，正在进入...' : '登录成功，正在进入...'
    setTimeout(() => router.push('/'), 600)
  } catch (e) {
    msg.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 50%, #0A6FB8 100%);
  padding: 140px 20px;
  overflow: hidden;
}

/* 动态气泡背景 */
.bg-bubbles {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}
.bubble {
  position: absolute;
  bottom: -80px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  animation: float-up 12s linear infinite;
}
.bubble.b1 { left: 8%;  width: 50px; height: 50px; animation-duration: 14s; }
.bubble.b2 { left: 22%; width: 30px; height: 30px; animation-duration: 10s; animation-delay: 1s; }
.bubble.b3 { left: 38%; width: 60px; height: 60px; animation-duration: 16s; animation-delay: 2s; }
.bubble.b4 { left: 55%; width: 35px; height: 35px; animation-duration: 11s; animation-delay: 0.5s; }
.bubble.b5 { left: 72%; width: 45px; height: 45px; animation-duration: 13s; animation-delay: 3s; }
.bubble.b6 { left: 88%; width: 25px; height: 25px; animation-duration: 9s;  animation-delay: 1.5s; }

@keyframes float-up {
  0%   { transform: translateY(0) scale(1); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.6; }
  100% { transform: translateY(-700px) scale(1.3); opacity: 0; }
}

.login-card {
  position: relative;
  z-index: 1;
  display: flex;
  width: 720px;
  max-width: 100%;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .25), 0 0 0 1px rgba(255,255,255,.1);
  animation: card-in 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* 品牌区 */
.brand-side {
  width: 320px;
  background: linear-gradient(135deg, #12B7F5 0%, #1AA1E6 60%, #0D8BD9 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.brand-side::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
  animation: rotate-bg 20s linear infinite;
}
@keyframes rotate-bg {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.brand-side > * { position: relative; z-index: 1; }
.brand-logo {
  font-size: 56px;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.2));
  animation: bounce-logo 2.5s ease-in-out infinite;
}
@keyframes bounce-logo {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-6px); }
}
.brand-side h2 {
  font-size: 19px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px rgba(0,0,0,.15);
}
.brand-side p {
  font-size: 12px;
  opacity: .9;
  line-height: 1.7;
}
.brand-features {
  margin-top: 20px;
  text-align: left;
  width: 100%;
  padding: 0 16px;
  box-sizing: border-box;
}
.feat {
  font-size: 12px;
  opacity: .95;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}
.feat span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  margin-right: 8px;
  font-size: 10px;
  font-weight: 700;
}
.brand-sub {
  margin-top: 24px;
  font-size: 11px;
  opacity: .75;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.2);
  width: 80%;
}

/* 表单区 */
.form-side {
  flex: 1;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-header {
  text-align: center;
  margin-bottom: 28px;
}
.avatar {
  width: 60px;
  height: 60px;
  margin: 0 auto 12px;
  background: linear-gradient(135deg, #f0f7ff 0%, #d8ecff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 4px 14px rgba(18, 183, 245, 0.2);
  border: 2px solid #fff;
}
.form-side h3 {
  font-size: 20px;
  color: #1a1a2e;
  margin-bottom: 4px;
  font-weight: 700;
}
.form-tip {
  font-size: 12px;
  color: #999;
}

.field {
  display: flex;
  align-items: center;
  border: 1.5px solid #e8e8e8;
  border-radius: 10px;
  padding: 0 14px;
  margin-bottom: 14px;
  transition: all 0.25s ease;
  background: #fafbfc;
}
.field:focus-within {
  border-color: #12B7F5;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(18, 183, 245, 0.1);
  transform: translateY(-1px);
}
.field .icon { font-size: 15px; opacity: .5; transition: opacity .2s; }
.field:focus-within .icon { opacity: 1; }
.field input {
  flex: 1;
  border: none;
  outline: none;
  padding: 11px 10px;
  font-size: 13px;
  background: transparent;
  color: #333;
}
.field input::placeholder { color: #bbb; }
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
}
.msg.ok { color: #2e7d32; background: #e8f5e9; }
.msg.ok .msg-icon { background: #4caf50; color: #fff; }
.msg.err { color: #c62828; background: #ffebee; }
.msg.err .msg-icon { background: #f44336; color: #fff; }

.msg-fade-enter-active, .msg-fade-leave-active {
  transition: all 0.3s ease;
}
.msg-fade-enter-from, .msg-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.btn-submit {
  position: relative;
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #12B7F5 0%, #0D8BD9 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-top: 6px;
  overflow: hidden;
  letter-spacing: 2px;
  box-shadow: 0 4px 14px rgba(18, 183, 245, 0.35);
}
.btn-submit::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s;
}
.btn-submit:hover::before { left: 100%; }
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

.switch-mode {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #999;
}
.switch-mode a {
  color: #12B7F5;
  text-decoration: none;
  margin-left: 4px;
  font-weight: 600;
  transition: color .2s;
}
.switch-mode a:hover { color: #0D8BD9; text-decoration: underline; }

.admin-entry {
  text-align: center;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #eee;
}
.admin-entry a {
  color: #999;
  text-decoration: none;
  font-size: 12px;
  transition: color .2s;
}
.admin-entry a:hover { color: #1a1a2e; }

@media (max-width: 540px) {
  .login-card { flex-direction: column; width: 340px; }
  .brand-side { width: 100%; padding: 28px; }
  .brand-logo { font-size: 42px; margin-bottom: 8px; }
  .brand-features { display: none; }
  .brand-sub { border-top: none; padding-top: 0; margin-top: 12px; }
  .form-side { padding: 28px 24px; }
}
</style>

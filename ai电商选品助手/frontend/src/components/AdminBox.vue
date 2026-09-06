<template>
  <div class="user-box" v-if="adminState.admin" @click="open = !open" v-click-outside="close">
    <div class="avatar" :style="{ background: `linear-gradient(135deg, ${c[0]}, ${c[1]})` }">
      {{ avatarText(adminState.admin.username) }}
    </div>
    <span class="nick">🛡 {{ adminState.admin.username }}</span>
    <span class="caret">▾</span>

    <transition name="pop">
      <div class="panel" v-if="open" @click.stop>
        <div class="panel-head">
          <div class="avatar lg" :style="{ background: `linear-gradient(135deg, ${c[0]}, ${c[1]})` }">
            {{ avatarText(adminState.admin.username) }}
          </div>
          <div class="info">
            <div class="p-nick">🛡 {{ adminState.admin.username }}</div>
            <div class="p-account">管理员 · {{ adminState.admin.role }}</div>
          </div>
        </div>
        <div class="panel-body">
          <div class="row"><span class="k">账号</span><span class="v">{{ adminState.admin.username }}</span></div>
          <div class="row" v-if="adminState.admin.last_login">
            <span class="k">最近登录</span>
            <span class="v">{{ adminState.admin.last_login.slice(0, 19).replace('T', ' ') }}</span>
          </div>
          <div class="row" v-if="adminState.admin.created_at">
            <span class="k">注册时间</span><span class="v">{{ adminState.admin.created_at.slice(0, 10) }}</span>
          </div>
        </div>
        <div class="panel-foot">
          <button class="btn-logout" @click="onLogout">退出登录</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { adminState, clearAdminAuth, avatarColors, avatarText } from '../auth'

const router = useRouter()
const open = ref(false)
const c = avatarColors(adminState.admin?.username || '')

function close() { open.value = false }

function onLogout() {
  clearAdminAuth()
  open.value = false
  router.push('/admin/login')
}

const vClickOutside = {
  mounted(el) {
    el._handler = (e) => { if (!el.contains(e.target)) el.__close?.() }
    el.__close = close
    document.addEventListener('click', el._handler)
  },
  unmounted(el) { document.removeEventListener('click', el._handler) },
}
</script>

<style scoped>
.user-box { position: relative; display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; cursor: pointer; transition: background .2s; }
.user-box:hover { background: var(--primary-50); }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 15px; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,.12); }
.avatar.lg { width: 56px; height: 56px; font-size: 26px; box-shadow: 0 4px 14px rgba(0,0,0,.18); }
.nick { font-size: 14px; color: var(--text); max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.caret { font-size: 11px; color: var(--text-mute); }
.panel { position: absolute; top: calc(100% + 8px); right: 0; width: 280px; background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); border: 1px solid var(--border); overflow: hidden; z-index: 100; }
.panel-head { display: flex; align-items: center; gap: 14px; padding: 20px; background: var(--primary-grad); color: #fff; }
.p-nick { font-size: 17px; font-weight: 600; }
.p-account { font-size: 12px; opacity: .85; margin-top: 2px; }
.panel-body { padding: 16px 20px; }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: var(--text-mute); }
.v { color: var(--text); max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.panel-foot { padding: 12px 20px 16px; }
.btn-logout { width: 100%; padding: 10px; background: #fff; border: 1px solid var(--accent-red); color: var(--accent-red); border-radius: var(--radius-sm); font-size: 14px; cursor: pointer; transition: all .2s; font-weight: 500; }
.btn-logout:hover { background: var(--accent-red); color: #fff; }
.pop-enter-active, .pop-leave-active { transition: opacity .15s, transform .15s; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-6px); }
</style>

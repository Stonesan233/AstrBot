<template>
  <div class="studio-page">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="d-flex align-center ga-2">
        <v-icon icon="mdi-account-group" color="primary" />
        <h2 class="text-h5 font-weight-bold">Studio 工作室</h2>
        <v-chip size="x-small" color="orange-darken-2" variant="tonal" label>Beta</v-chip>
      </div>
      <div class="d-flex align-center ga-3">
        <v-switch v-model="autoRefresh" label="自动刷新" color="primary" hide-details inset density="compact" />
        <v-btn variant="text" color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="loadAll">刷新</v-btn>
        <v-btn variant="flat" color="primary" prepend-icon="mdi-plus" @click="showAddMember = true">添加成员</v-btn>
      </div>
    </div>

    <!-- Alerts -->
    <v-alert v-if="apiError" type="error" variant="tonal" class="mb-3 rounded-lg" density="compact" closable @click:close="apiError = ''">{{ apiError }}</v-alert>
    <v-alert v-if="!loading && !status.engineReady" type="warning" variant="tonal" class="mb-3 rounded-lg" density="compact">执行引擎未连接</v-alert>

    <v-row>
      <!-- ====== Left: Members ====== -->
      <v-col cols="12" md="3">
        <v-card class="rounded-lg border-thin fill-height" variant="flat" border>
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-account-group" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">成员</span>
            </div>
            <v-chip size="x-small" variant="tonal" color="primary">{{ members.length }}</v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-2">
            <div v-if="loading && members.length === 0" class="pa-4"><v-skeleton-loader type="list-item@2" /></div>
            <v-list-item
              v-for="m in members"
              :key="m.name"
              class="rounded-lg mb-1"
              @click="mentionMember(m.name)"
            >
              <template #prepend>
                <v-avatar :color="getMemberColor(m.name)" size="34" class="mr-3">
                  <span class="text-white text-body-2 font-weight-bold">{{ m.name[0] }}</span>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2 font-weight-medium">{{ m.name }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption text-medium-emphasis text-truncate">{{ truncate(m.persona_prompt, 28) }}</v-list-item-subtitle>
              <template #append>
                <v-icon icon="mdi-at" size="x-small" color="primary" />
              </template>
            </v-list-item>
            <div v-if="members.length === 0" class="text-center py-6 text-medium-emphasis">
              <v-icon icon="mdi-account-off-outline" size="40" class="mb-2 opacity-40" />
              <div class="text-caption">暂无成员</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ====== Center: Chat Timeline ====== -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg border-thin" variant="flat" border>
          <!-- Title -->
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-forum-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="activeConv" size="x-small" :color="convStatusColor" variant="tonal">{{ convStatusLabel }}</v-chip>
              <span v-if="isConvActive" class="live-dot" />
            </div>
            <div class="d-flex align-center ga-2">
              <span v-if="activeConv" class="text-caption text-medium-emphasis">{{ activeConv.turns.length }} / {{ activeConv.max_rounds }}</span>
              <v-btn v-if="activeConv" icon="mdi-delete-outline" variant="text" size="small" color="error" @click="resetConversation">
                <v-tooltip activator="parent" location="top">重置</v-tooltip>
              </v-btn>
            </div>
          </v-card-title>
          <v-divider />

          <!-- Messages area -->
          <div class="chat-log pa-4" ref="chatLogRef">
            <div v-if="loading && !activeConv" class="pa-4"><v-skeleton-loader type="card@2" /></div>

            <div v-else-if="!activeConv || turns.length === 0" class="text-center py-12 text-medium-emphasis">
              <v-icon icon="mdi-chat-processing-outline" size="56" class="mb-3 opacity-20" />
              <div class="text-body-2">暂无协作记录</div>
              <div class="text-caption mt-1">在下方输入任务启动协作</div>
            </div>

            <v-timeline v-else side="end" density="compact" align="start">
              <v-timeline-item
                v-for="(turn, idx) in turns"
                :key="turn.timestamp + '-' + idx"
                :dot-color="getMemberColor(turn.to_member)"
                size="small"
                class="turn-item"
              >
                <template #icon>
                  <v-icon :icon="turn.auto_delegated ? 'mdi-auto-fix' : 'mdi-circle-small'" :color="turn.auto_delegated ? 'orange' : undefined" size="small" />
                </template>

                <!-- Header line -->
                <div class="d-flex align-center ga-2 mb-1">
                  <v-avatar :color="getMemberColor(turn.to_member)" size="22">
                    <span class="text-white font-weight-bold" style="font-size:10px">{{ turn.to_member[0] }}</span>
                  </v-avatar>
                  <span class="text-body-2 font-weight-bold" :style="{ color: memberTextColor(turn.to_member) }">{{ turn.to_member }}</span>
                  <v-chip v-if="turn.auto_delegated" size="x-small" variant="tonal" color="orange" label>自动</v-chip>
                  <span class="text-caption text-medium-emphasis ml-auto">R{{ idx + 1 }}</span>
                  <span class="text-caption text-medium-emphasis">{{ formatTime(turn.timestamp) }}</span>
                </div>

                <!-- Task -->
                <div class="msg-bubble task-bubble pa-3 rounded-lg mb-2">
                  <div class="d-flex align-center ga-1 mb-1">
                    <v-icon icon="mdi-clipboard-text" size="x-small" color="primary" />
                    <span class="text-caption font-weight-bold text-primary">任务</span>
                    <span class="text-caption text-medium-emphasis ml-auto">from {{ turn.from_member }}</span>
                  </div>
                  <div class="text-body-2">{{ turn.message }}</div>
                </div>

                <!-- Response -->
                <div class="msg-bubble pa-3 rounded-lg mb-2">
                  <div class="d-flex align-center ga-1 mb-1">
                    <v-icon icon="mdi-robot-outline" size="x-small" color="medium-emphasis" />
                    <span class="text-caption font-weight-bold text-medium-emphasis">回复</span>
                    <v-spacer />
                    <v-btn icon="mdi-content-copy" variant="text" size="x-small" color="grey" @click="copyText(turn.response)">
                      <v-tooltip activator="parent" location="top">复制</v-tooltip>
                    </v-btn>
                  </div>
                  <div class="response-text">
                    <template v-if="hasCode(turn.response)">
                      <template v-for="(seg, si) in parseCode(turn.response)" :key="si">
                        <pre v-if="seg.type === 'code'" class="code-block rounded pa-2 mb-1"><code>{{ seg.content }}</code></pre>
                        <span v-else>{{ seg.content }}</span>
                      </template>
                    </template>
                    <template v-else>{{ turn.response }}</template>
                  </div>
                </div>

                <!-- Delegation arrow -->
                <div v-if="turn.delegated_to" class="delegation-arrow d-flex align-center ga-2 mt-1 pa-2 rounded-lg">
                  <v-icon :icon="turn.auto_delegated ? 'mdi-swap-horizontal-bold' : 'mdi-arrow-right-bold-circle'" size="small" :color="turn.auto_delegated ? 'orange' : 'primary'" />
                  <v-chip size="x-small" :color="getMemberColor(turn.to_member)" variant="tonal">{{ turn.to_member }}</v-chip>
                  <v-icon icon="mdi-arrow-right" size="x-small" color="primary" />
                  <v-chip size="x-small" :color="getMemberColor(turn.delegated_to)" variant="tonal">{{ turn.delegated_to }}</v-chip>
                  <span v-if="turn.auto_delegated" class="text-caption text-orange font-weight-bold">自动委托</span>
                </div>
              </v-timeline-item>
            </v-timeline>
          </div>

          <!-- Input bar -->
          <v-divider />
          <div class="pa-3">
            <div class="d-flex align-center ga-2">
              <v-chip v-if="chatTarget" size="small" :color="getMemberColor(chatTarget)" variant="tonal" closable @click:close="chatTarget = ''">
                @{{ chatTarget }}
              </v-chip>
              <v-text-field
                v-model="chatInput"
                placeholder="输入任务... (点击左侧 @成员)"
                variant="outlined"
                density="compact"
                hide-details
                :disabled="sendingChat || isConvActive"
                @keydown.enter="sendChat"
              >
                <template #prepend-inner><v-icon icon="mdi-message-text-outline" size="small" /></template>
              </v-text-field>
              <v-btn
                variant="flat"
                color="primary"
                :loading="sendingChat"
                :disabled="!chatInput.trim() || isConvActive"
                icon="mdi-send"
                size="small"
                @click="sendChat"
              >
                <v-tooltip activator="parent" location="top">发送 (Enter)</v-tooltip>
              </v-btn>
            </div>
            <div v-if="isConvActive" class="text-caption text-info mt-2 d-flex align-center ga-1">
              <span class="live-dot" style="width:6px;height:6px" /> 协作进行中...
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- ====== Right: Status ====== -->
      <v-col cols="12" md="3">
        <div class="d-flex flex-column ga-4">
          <v-card class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-information-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">任务状态</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-3">
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">执行引擎</span>
                  <v-chip :color="status.engineReady ? 'success' : 'error'" size="small" variant="tonal">{{ status.engineReady ? '已连接' : '未连接' }}</v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">自动委托</span>
                  <v-chip :color="status.autoDelegate ? 'success' : 'grey'" size="small" variant="tonal">{{ status.autoDelegate ? '开' : '关' }}</v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">轮次上限</span>
                  <span class="text-body-2 font-weight-bold">{{ status.maxRounds }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">活跃会话</span>
                  <span class="text-body-2 font-weight-bold">{{ status.activeCount }} / {{ status.totalCount }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Context -->
          <v-card v-if="activeConv" class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-brain" size="small" color="deep-purple" />
              <span class="text-subtitle-2 font-weight-bold">上下文</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-3">
                <div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis">进度</span>
                    <span class="text-caption font-weight-bold">{{ activeConv.turns.length }} / {{ activeConv.max_rounds }}</span>
                  </div>
                  <v-progress-linear :model-value="progressPct" :color="progressClr" height="6" rounded />
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">最近修改</span>
                  <v-chip v-if="activeConv.last_modified_by" size="small" :color="getMemberColor(activeConv.last_modified_by)" variant="tonal">{{ activeConv.last_modified_by }}</v-chip>
                  <span v-else class="text-caption text-medium-emphasis">-</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">最近审查</span>
                  <v-chip v-if="activeConv.last_review_by" size="small" :color="getMemberColor(activeConv.last_review_by)" variant="tonal">{{ activeConv.last_review_by }}</v-chip>
                  <span v-else class="text-caption text-medium-emphasis">-</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">自动委托次数</span>
                  <v-chip size="small" variant="tonal" color="orange">{{ activeConv.auto_delegate_count || 0 }}</v-chip>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </v-col>
    </v-row>

    <!-- Add Member Dialog -->
    <v-dialog v-model="showAddMember" max-width="500">
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center justify-space-between py-4 px-6">
          <span class="text-h6">添加成员</span>
          <v-btn icon="mdi-close" variant="text" @click="showAddMember = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-text-field v-model="newMember.name" label="名称" variant="outlined" density="comfortable" prepend-inner-icon="mdi-account" class="mb-4" />
          <v-textarea v-model="newMember.persona" label="人格提示词" variant="outlined" density="comfortable" auto-grow rows="3" prepend-inner-icon="mdi-text" placeholder="专业能力和风格..." />
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showAddMember = false">取消</v-btn>
          <v-btn variant="flat" color="primary" :loading="addingMember" @click="addMember">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="top">
      {{ snackbar.message }}
      <template #actions><v-btn variant="text" @click="snackbar.show = false">关闭</v-btn></template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Turn = {
  from_member: string
  to_member: string
  message: string
  response: string
  delegated_to: string | null
  auto_delegated: boolean
  timestamp: number
}

type Conv = {
  id: string
  turns: Turn[]
  status: string
  max_rounds: number
  created_at: number
  updated_at: number
  last_modified_by: string | null
  last_review_by: string | null
  auto_delegate_count: number
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const loading = ref(false)
const addingMember = ref(false)
const autoRefresh = ref(true)
const showAddMember = ref(false)
const chatLogRef = ref<HTMLElement | null>(null)
const apiError = ref('')
const snackbar = ref({ show: false, message: '', color: 'success' })

const status = ref({
  engineReady: false,
  autoDelegate: false,
  autoStop: false,
  maxRounds: 10,
  activeCount: 0,
  totalCount: 0,
})

const members = ref<{ name: string; persona_prompt: string }[]>([])
const activeConv = ref<Conv | null>(null)

const chatInput = ref('')
const chatTarget = ref('')
const sendingChat = ref(false)

const newMember = ref({ name: '', persona: '' })

let pollTimer: ReturnType<typeof setInterval> | null = null

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------

const turns = computed(() => activeConv.value?.turns ?? [])
const isConvActive = computed(() => activeConv.value?.status === 'active')

const convStatusColor = computed(() => {
  const m: Record<string, string> = { active: 'info', completed: 'success', timeout: 'warning', error: 'error', idle: 'grey' }
  return m[activeConv.value?.status ?? ''] ?? 'grey'
})
const convStatusLabel = computed(() => {
  const m: Record<string, string> = { active: '进行中', completed: '已完成', timeout: '超时', error: '错误', idle: '空闲' }
  return m[activeConv.value?.status ?? ''] ?? ''
})

const progressPct = computed(() => {
  if (!activeConv.value) return 0
  return Math.min((activeConv.value.turns.length / activeConv.value.max_rounds) * 100, 100)
})
const progressClr = computed(() => {
  if (!activeConv.value) return 'primary'
  const r = activeConv.value.turns.length / activeConv.value.max_rounds
  return r >= 1 ? 'error' : r >= 0.7 ? 'warning' : 'primary'
})

// ---------------------------------------------------------------------------
// Member colors — deterministic per name
// ---------------------------------------------------------------------------

const _cm: Record<string, string> = {}
// Named members get fixed colors; others cycle palette
const _named: Record<string, string> = { '露娜': 'deep-purple', '露娜大人': 'deep-purple', '朝日': 'pink', '朝日娘': 'pink' }
const _palette = ['deep-purple', 'blue', 'teal', 'indigo', 'cyan', 'pink', 'orange', 'green', 'brown', 'blue-grey']

function getMemberColor(name: string): string {
  if (_cm[name]) return _cm[name]
  _cm[name] = _named[name] ?? _palette[Object.keys(_cm).length % _palette.length]
  return _cm[name]
}

function memberTextColor(name: string): string {
  const map: Record<string, string> = {
    'deep-purple': '#5e35b1', blue: '#1565c0', teal: '#00897b', indigo: '#3949ab',
    cyan: '#0097a7', pink: '#d81b60', orange: '#ef6c00', green: '#2e7d32',
    brown: '#6d4c41', 'blue-grey': '#455a64',
  }
  return map[getMemberColor(name)] ?? '#333'
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function truncate(t: string, n: number) { return !t ? '' : t.length > n ? t.substring(0, n) + '...' : t }

function formatTime(ts: number): string {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function toast(msg: string, color = 'success') { snackbar.value = { show: true, message: msg, color } }
function copyText(t: string) { navigator.clipboard.writeText(t).then(() => toast('已复制')).catch(() => {}) }
function mentionMember(name: string) { chatTarget.value = name }

function scrollToBottom() {
  nextTick(() => { const el = chatLogRef.value; if (el) el.scrollTop = el.scrollHeight })
}

// ---------------------------------------------------------------------------
// Code block parser
// ---------------------------------------------------------------------------

const _codeRe = /```[\w]*\n([\s\S]*?)```/g

function hasCode(t: string): boolean { _codeRe.lastIndex = 0; return _codeRe.test(t) }

function parseCode(t: string): { type: 'text' | 'code'; content: string }[] {
  const segs: { type: 'text' | 'code'; content: string }[] = []
  let last = 0; _codeRe.lastIndex = 0; let m: RegExpExecArray | null
  while ((m = _codeRe.exec(t)) !== null) {
    if (m.index > last) segs.push({ type: 'text', content: t.slice(last, m.index) })
    segs.push({ type: 'code', content: m[1].trim() }); last = m.index + m[0].length
  }
  if (last < t.length) segs.push({ type: 'text', content: t.slice(last) })
  return segs.length ? segs : [{ type: 'text', content: t }]
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function loadStatus() {
  try {
    const r = await axios.get('/api/studio/status')
    if (r.data.status === 'ok') {
      const d = r.data.data
      status.value = {
        engineReady: !!d.engine_ok,
        autoDelegate: d.auto_delegate !== false,
        autoStop: d.auto_stop !== false,
        maxRounds: d.max_rounds || 10,
        activeCount: d.active_count || 0,
        totalCount: d.total_count || 0,
      }
      if (d.members && typeof d.members === 'object') {
        members.value = Object.entries(d.members).map(([name, info]: [string, any]) => ({
          name, persona_prompt: info.persona_prompt || '',
        }))
      }
      apiError.value = ''
    }
  } catch (e: any) {
    if (e?.response?.status === 404) apiError.value = 'Studio API 未就绪'
  }
}

async function loadHistory() {
  try {
    const r = await axios.get('/api/studio/history')
    if (r.data.status === 'ok') {
      const data = r.data.data
      if (data && typeof data === 'object') {
        const all = Object.values(data) as Conv[]
        const active = all.filter(c => c.turns?.length > 0).sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
        const prev = activeConv.value?.turns.length ?? 0
        activeConv.value = active[0] || null
        if (activeConv.value && activeConv.value.turns.length > prev) scrollToBottom()
      }
    }
  } catch (e: any) {
    console.warn('history poll error:', e?.message)
  }
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text || isConvActive.value) return
  const full = chatTarget.value ? `@${chatTarget.value} ${text}` : text
  sendingChat.value = true
  try {
    const r = await axios.post('/api/studio/chat', { message: full })
    if (r.data.status === 'ok') {
      chatInput.value = ''
      toast('协作已启动')
      await loadHistory()
    } else {
      toast(r.data.message || '发送失败', 'error')
    }
  } catch (e: any) {
    toast(e?.response?.data?.message || '发送失败', 'error')
  } finally {
    sendingChat.value = false
  }
}

async function addMember() {
  if (!newMember.value.name.trim() || !newMember.value.persona.trim()) { toast('请填写完整', 'warning'); return }
  addingMember.value = true
  try {
    const r = await axios.post('/api/studio/member', { name: newMember.value.name.trim(), persona_prompt: newMember.value.persona.trim() })
    if (r.data.status === 'ok') { toast('添加成功'); showAddMember.value = false; newMember.value = { name: '', persona: '' }; await loadAll() }
    else toast(r.data.message || '失败', 'error')
  } catch (e: any) { toast(e?.response?.data?.message || '失败', 'error') }
  finally { addingMember.value = false }
}

async function resetConversation() {
  try {
    const r = await axios.post('/api/studio/reset')
    if (r.data.status === 'ok') { toast('已重置'); activeConv.value = null; await loadAll() }
  } catch (e: any) { toast('重置失败', 'error') }
}

async function loadAll() {
  loading.value = true
  try { await Promise.all([loadStatus(), loadHistory()]) }
  finally { loading.value = false }
}

// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------

watch(autoRefresh, v => v ? startPoll() : stopPoll())

function startPoll() {
  stopPoll()
  pollTimer = setInterval(() => { loadStatus(); loadHistory() }, 2000)
}

function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => { loadAll(); if (autoRefresh.value) startPoll() })
onUnmounted(() => stopPoll())
</script>

<style scoped>
.studio-page { padding: 24px; max-width: 1600px; margin: 0 auto; }

.chat-log { height: 520px; overflow-y: auto; scroll-behavior: smooth; }
.chat-log::-webkit-scrollbar { width: 5px; }
.chat-log::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 5px; }

.turn-item { animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.msg-bubble { background: rgba(var(--v-theme-on-surface), 0.025); border: 1px solid rgba(0,0,0,0.06); }
.task-bubble { border-left: 3px solid rgb(var(--v-theme-primary)) !important; }

.response-text {
  white-space: pre-wrap; word-break: break-word;
  max-height: 250px; overflow-y: auto;
  font-size: 0.85rem; line-height: 1.55;
}
.response-text::-webkit-scrollbar { width: 3px; }
.response-text::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.08); border-radius: 3px; }

.code-block {
  background: #1e1e1e; color: #d4d4d4;
  font-family: 'Cascadia Code','Fira Code','Consolas',monospace;
  font-size: 0.8rem; line-height: 1.4; overflow-x: auto;
}

.delegation-arrow {
  background: linear-gradient(90deg, rgba(var(--v-theme-primary),0.08), transparent);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #4caf50; display: inline-block;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(1.4); } }
</style>

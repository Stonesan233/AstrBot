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

      <!-- ====== Center: Chat History (v-timeline) ====== -->
      <v-col cols="12" md="6">
        <v-card class="chat-card rounded-lg border-thin d-flex flex-column" variant="flat" border>
          <!-- Title bar -->
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4 flex-shrink-0">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-forum-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="isConvActive" size="x-small" color="info" variant="tonal">进行中</v-chip>
              <span v-if="isConvActive" class="live-dot" />
              <span v-if="taskGroups.length > 0" class="text-caption text-medium-emphasis">{{ taskGroups.length }} 个任务</span>
            </div>
            <div class="d-flex align-center ga-2">
              <v-btn icon="mdi-delete-sweep-outline" variant="text" size="small" color="error" @click="resetConversation">
                <v-tooltip activator="parent" location="top">清空所有记录</v-tooltip>
              </v-btn>
            </div>
          </v-card-title>
          <v-divider />

          <!-- Timeline messages area -->
          <div class="chat-messages flex-grow-1" ref="chatLogRef">
            <!-- Loading skeleton -->
            <div v-if="loading && allTurns.length === 0" class="pa-4">
              <v-skeleton-loader type="card@3" />
            </div>

            <!-- Empty state -->
            <div v-else-if="allTurns.length === 0" class="d-flex flex-column align-center justify-center fill-height text-medium-emphasis">
              <v-icon icon="mdi-chat-processing-outline" size="56" class="mb-3 opacity-20" />
              <div class="text-body-2">暂无协作记录</div>
              <div class="text-caption mt-1">在下方输入任务启动协作</div>
            </div>

            <!-- v-timeline with all history -->
            <div v-else class="pa-4">
              <v-timeline side="end" density="compact" align="start">
                <template v-for="(msg, idx) in chatMessages" :key="msg.id">
                  <!-- Task group separator -->
                  <v-timeline-item
                    v-if="msg.type === 'task-header'"
                    size="small"
                    dot-color="primary"
                    class="task-header-item"
                  >
                    <template #icon>
                      <v-icon icon="mdi-play-circle-outline" size="16" color="white" />
                    </template>
                    <div class="d-flex align-center ga-2 my-1">
                      <v-chip size="x-small" variant="tonal" color="primary" label>
                        任务 #{{ (msg.taskIndex ?? 0) + 1 }}
                      </v-chip>
                      <span class="text-caption text-medium-emphasis">{{ formatTime(msg.time) }}</span>
                      <v-chip v-if="msg.isActive" size="x-small" variant="tonal" color="info" label>
                        <span class="live-dot-sm" /> 进行中
                      </v-chip>
                      <v-chip v-else size="x-small" variant="tonal" color="success" label>已完成</v-chip>
                      <span class="text-caption text-medium-emphasis">{{ msg.from }} → {{ msg.to }}</span>
                    </div>
                  </v-timeline-item>

                  <!-- Task message bubble -->
                  <v-timeline-item
                    v-else-if="msg.type === 'task'"
                    :dot-color="getMemberColor(msg.sender)"
                    size="x-small"
                  >
                    <div class="chat-bubble left-bubble" :style="bubbleStyle(msg)">
                      <div class="d-flex align-center ga-1 mb-1">
                        <v-icon icon="mdi-clipboard-text-outline" size="14" :color="getMemberColor(msg.sender)" />
                        <span class="text-caption font-weight-bold">任务</span>
                        <span class="text-caption text-medium-emphasis ml-auto">from {{ msg.sender }}</span>
                      </div>
                      <div class="msg-text">{{ msg.content }}</div>
                    </div>
                  </v-timeline-item>

                  <!-- Response message bubble -->
                  <v-timeline-item
                    v-else-if="msg.type === 'response'"
                    :dot-color="getMemberColor(msg.sender)"
                    size="x-small"
                  >
                    <div class="chat-bubble left-bubble" :style="bubbleStyle(msg)">
                      <div class="d-flex align-center ga-1 mb-1">
                        <v-avatar :color="getMemberColor(msg.sender)" size="18">
                          <span class="text-white font-weight-bold" style="font-size:9px">{{ msg.sender[0] }}</span>
                        </v-avatar>
                        <span class="chat-name font-weight-bold" :style="{ color: memberTextColor(msg.sender), fontSize: '0.8rem' }">{{ msg.sender }}</span>
                        <span class="text-caption text-medium-emphasis ml-auto">{{ formatTime(msg.time) }}</span>
                      </div>
                      <div v-if="hasCode(msg.content)" class="response-text">
                        <template v-for="(seg, si) in parseCode(msg.content)" :key="si">
                          <pre v-if="seg.type === 'code'" class="code-block rounded pa-2 mb-1"><code>{{ seg.content }}</code></pre>
                          <span v-else style="white-space:pre-wrap">{{ seg.content }}</span>
                        </template>
                      </div>
                      <div v-else class="response-text">{{ msg.content }}</div>
                      <div class="d-flex mt-1" style="justify-content:flex-end">
                        <v-btn icon="mdi-content-copy" variant="text" size="x-small" color="grey" density="compact" @click="copyText(msg.content)">
                          <v-tooltip activator="parent" location="bottom">复制</v-tooltip>
                        </v-btn>
                      </div>
                    </div>
                  </v-timeline-item>

                  <!-- Delegation indicator -->
                  <v-timeline-item
                    v-else-if="msg.type === 'system'"
                    size="x-small"
                    :dot-color="msg.autoDelegated ? 'orange' : 'primary'"
                  >
                    <div class="d-flex align-center ga-1 my-1 px-2 py-1 rounded-pill delegation-pill">
                      <v-chip size="x-small" :color="getMemberColor(msg.sender)" variant="tonal" label>{{ msg.sender }}</v-chip>
                      <v-icon :icon="msg.autoDelegated ? 'mdi-swap-horizontal-bold' : 'mdi-arrow-right'" size="small" :color="msg.autoDelegated ? 'orange' : 'primary'" />
                      <v-chip size="x-small" :color="getMemberColor(msg.delegateTo || '')" variant="tonal" label>{{ msg.delegateTo }}</v-chip>
                      <v-chip v-if="msg.autoDelegated" size="x-small" variant="tonal" color="orange" label>LLM自主</v-chip>
                    </div>
                  </v-timeline-item>
                </template>
              </v-timeline>
            </div>
          </div>

          <!-- Input bar -->
          <v-divider />
          <div class="pa-3 flex-shrink-0">
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
                  <span class="text-body-2 text-medium-emphasis">LLM 自主委托</span>
                  <v-chip :color="status.autoDelegate ? 'success' : 'grey'" size="small" variant="tonal">{{ status.autoDelegate ? '开' : '关' }}</v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">轮次上限</span>
                  <span class="text-body-2 font-weight-bold">{{ status.maxRounds }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">历史任务</span>
                  <span class="text-body-2 font-weight-bold">{{ taskGroups.length }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Current task context -->
          <v-card v-if="currentTaskTurns.length > 0" class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-brain" size="small" color="deep-purple" />
              <span class="text-subtitle-2 font-weight-bold">当前任务</span>
              <v-chip v-if="isConvActive" size="x-small" color="info" variant="tonal">进行中</v-chip>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-3">
                <div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis">进度</span>
                    <span class="text-caption font-weight-bold">{{ currentTaskTurns.length }} / {{ status.maxRounds }}</span>
                  </div>
                  <v-progress-linear :model-value="currentProgressPct" :color="currentProgressClr" height="6" rounded />
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </v-col>
    </v-row>

    <!-- Add Member Dialog -->
    <v-dialog v-model="showAddMember" max-width="560">
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center justify-space-between py-4 px-6">
          <span class="text-h6">添加成员</span>
          <v-btn icon="mdi-close" variant="text" @click="showAddMember = false" />
        </v-card-title>
        <v-divider />

        <!-- Tab: SubAgent bind / Manual -->
        <v-tabs v-model="addMemberTab" density="compact" class="px-4">
          <v-tab value="subagent">绑定 SubAgent</v-tab>
          <v-tab value="manual">手动添加</v-tab>
        </v-tabs>
        <v-divider />

        <!-- SubAgent bind tab -->
        <v-card-text v-if="addMemberTab === 'subagent'" class="pa-4">
          <div v-if="loadingSubagents" class="text-center py-4">
            <v-progress-circular indeterminate size="24" color="primary" />
            <div class="text-caption text-medium-emphasis mt-2">加载 SubAgent 列表...</div>
          </div>
          <div v-else-if="availableSubagents.length === 0" class="text-center py-6 text-medium-emphasis">
            <v-icon icon="mdi-robot-outline" size="40" class="mb-2 opacity-40" />
            <div class="text-body-2">暂无可用 SubAgent</div>
            <div class="text-caption mt-1">请先在 SubAgent 管理页创建 SubAgent</div>
          </div>
          <div v-else>
            <div
              v-for="sa in availableSubagents"
              :key="sa.name"
              class="d-flex align-center pa-3 mb-2 rounded-lg border-thin cursor-pointer"
              :class="{ 'bg-primary-lighten-5': isBound(sa.name) }"
              style="cursor: pointer"
              @click="bindSubAgent(sa)"
            >
              <v-avatar :color="getMemberColor(sa.name)" size="36" class="mr-3 flex-shrink-0">
                <span class="text-white font-weight-bold">{{ sa.name[0] }}</span>
              </v-avatar>
              <div class="flex-grow-1 overflow-hidden">
                <div class="text-body-2 font-weight-medium">{{ sa.name }}</div>
                <div class="text-caption text-medium-emphasis text-truncate">{{ sa.public_description || '无描述' }}</div>
              </div>
              <v-chip v-if="isBound(sa.name)" size="x-small" variant="tonal" color="success" class="ml-2">已绑定</v-chip>
              <v-btn v-else size="x-small" variant="tonal" color="primary" :loading="addingMember" @click.stop="bindSubAgent(sa)">绑定</v-btn>
            </div>
          </div>
        </v-card-text>

        <!-- Manual add tab -->
        <v-card-text v-if="addMemberTab === 'manual'" class="pa-6">
          <v-text-field v-model="newMember.name" label="名称" variant="outlined" density="comfortable" prepend-inner-icon="mdi-account" class="mb-4" />
          <v-textarea v-model="newMember.persona" label="人格提示词" variant="outlined" density="comfortable" auto-grow rows="3" prepend-inner-icon="mdi-text" placeholder="专业能力和风格..." />
        </v-card-text>

        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showAddMember = false">关闭</v-btn>
          <v-btn v-if="addMemberTab === 'manual'" variant="flat" color="primary" :loading="addingMember" @click="addMember">添加</v-btn>
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
  task_id: string
  from_member: string
  to_member: string
  message: string
  response: string
  delegated_to: string | null
  auto_delegated: boolean
  timestamp: number
  session_id?: string
}

type ChatMsg = {
  id: string
  sender: string
  content: string
  time: number
  type: 'task-header' | 'task' | 'response' | 'system'
  delegateTo?: string
  autoDelegated?: boolean
  side: 'left' | 'right'
  task_id: string
  taskIndex?: number
  isActive?: boolean
  from?: string
  to?: string
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
  maxRounds: 10,
})

const members = ref<{ name: string; persona_prompt: string }[]>([])

// All-history data
const allTurns = ref<Turn[]>([])
const activeTaskId = ref('')
const convStatus = ref('idle')

const chatInput = ref('')
const chatTarget = ref('')
const sendingChat = ref(false)

const addMemberTab = ref('subagent')
const availableSubagents = ref<{ name: string; persona_id: string; public_description: string; provider_id: string | null }[]>([])
const loadingSubagents = ref(false)

const newMember = ref({ name: '', persona: '' })

let pollTimer: ReturnType<typeof setInterval> | null = null

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------

const isConvActive = computed(() => convStatus.value === 'active')

// Group turns by task_id, preserving order
const taskGroups = computed(() => {
  const groups: { task_id: string; turns: Turn[] }[] = []
  let currentTaskId = ''
  for (const turn of allTurns.value) {
    const tid = turn.task_id || '_unknown'
    if (tid !== currentTaskId) {
      groups.push({ task_id: tid, turns: [] })
      currentTaskId = tid
    }
    groups[groups.length - 1].turns.push(turn)
  }
  return groups
})

// Turns for the currently active task (for progress display)
const currentTaskTurns = computed(() => {
  if (!activeTaskId.value) return []
  return allTurns.value.filter(t => t.task_id === activeTaskId.value)
})

const currentProgressPct = computed(() => {
  if (!currentTaskTurns.value.length) return 0
  return Math.min((currentTaskTurns.value.length / status.value.maxRounds) * 100, 100)
})

const currentProgressClr = computed(() => {
  const r = currentTaskTurns.value.length / status.value.maxRounds
  return r >= 1 ? 'error' : r >= 0.7 ? 'warning' : 'primary'
})

// ---------------------------------------------------------------------------
// Flatten all turns → chat messages (with task headers)
// ---------------------------------------------------------------------------

const chatMessages = computed<ChatMsg[]>(() => {
  const msgs: ChatMsg[] = []
  let prevTaskId = ''

  allTurns.value.forEach((turn, i) => {
    const tid = turn.task_id || '_unknown'

    // Task header when task_id changes
    if (tid !== prevTaskId) {
      msgs.push({
        id: `h-${tid}`,
        sender: turn.from_member,
        content: turn.message,
        time: turn.timestamp,
        type: 'task-header',
        side: 'left',
        task_id: tid,
        taskIndex: msgs.filter(m => m.type === 'task-header').length,
        isActive: tid === activeTaskId.value && isConvActive.value,
        from: turn.from_member,
        to: turn.to_member,
      })
      prevTaskId = tid
    }

    // Task message
    msgs.push({
      id: `t${i}-task`,
      sender: turn.from_member,
      content: turn.message,
      time: turn.timestamp,
      type: 'task',
      delegateTo: turn.to_member,
      side: getMemberSide(turn.from_member),
      task_id: tid,
    })

    // Response message
    msgs.push({
      id: `t${i}-resp`,
      sender: turn.to_member,
      content: turn.response,
      time: turn.timestamp,
      type: 'response',
      side: getMemberSide(turn.to_member),
      task_id: tid,
    })

    // Delegation indicator
    if (turn.delegated_to) {
      msgs.push({
        id: `t${i}-del`,
        sender: turn.to_member,
        content: '',
        time: turn.timestamp,
        type: 'system',
        delegateTo: turn.delegated_to,
        autoDelegated: turn.auto_delegated,
        side: getMemberSide(turn.to_member),
        task_id: tid,
      })
    }
  })

  return msgs
})

// ---------------------------------------------------------------------------
// Member colors — deterministic per name
// ---------------------------------------------------------------------------

const _cm: Record<string, string> = {}
const _named: Record<string, string> = { '露娜': 'deep-purple', '露娜大人': 'deep-purple', '朝日': 'pink', '朝日娘': 'pink' }
const _palette = ['deep-purple', 'blue', 'teal', 'indigo', 'cyan', 'pink', 'orange', 'green', 'brown', 'blue-grey']

function getMemberColor(name: string): string {
  if (!name) return 'grey'
  if (_cm[name]) return _cm[name]
  _cm[name] = _named[name] ?? _palette[Object.keys(_cm).length % _palette.length]
  return _cm[name]
}

const _textColorMap: Record<string, string> = {
  'deep-purple': '#5e35b1', blue: '#1565c0', teal: '#00897b', indigo: '#3949ab',
  cyan: '#0097a7', pink: '#d81b60', orange: '#ef6c00', green: '#2e7d32',
  brown: '#6d4c41', 'blue-grey': '#455a64', grey: '#757575',
}

function memberTextColor(name: string): string {
  return _textColorMap[getMemberColor(name)] ?? '#333'
}

// ---------------------------------------------------------------------------
// Member side (left / right)
// ---------------------------------------------------------------------------

const _namedSide: Record<string, 'left' | 'right'> = {
  '露娜': 'right', '露娜大人': 'right',
  '朝日': 'left', '朝日娘': 'left',
}

function getMemberSide(name: string): 'left' | 'right' {
  if (_namedSide[name]) return _namedSide[name]
  const idx = members.value.findIndex(m => m.name === name)
  if (idx >= 0) return idx % 2 === 0 ? 'left' : 'right'
  let h = 0
  for (const c of name) h = ((h << 5) - h + c.charCodeAt(0)) | 0
  return h % 2 === 0 ? 'left' : 'right'
}

// ---------------------------------------------------------------------------
// Bubble style per message
// ---------------------------------------------------------------------------

function bubbleStyle(msg: ChatMsg) {
  const c = memberTextColor(msg.sender)
  if (msg.side === 'right') {
    return { background: c + '15', borderRight: `3px solid ${c}60` }
  }
  return { background: c + '08', borderLeft: `3px solid ${c}50` }
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
        maxRounds: d.max_rounds || 10,
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
    const r = await axios.get('/api/studio/history', {
      params: { support_all_history: 'true' },
    })
    if (r.data.status === 'ok') {
      const data = r.data.data
      const prevLen = allTurns.value.length

      if (data && data.all_turns) {
        // New format: flat all_turns
        allTurns.value = data.all_turns
        activeTaskId.value = data.active_task_id || ''
        convStatus.value = data.active_session_status || 'idle'
      } else if (data && typeof data === 'object' && !data.all_turns) {
        // Fallback: old format (conversations dict)
        const all = Object.values(data) as any[]
        const withTurns = all.filter(c => c.turns?.length > 0).sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
        if (withTurns.length > 0) {
          const turns: Turn[] = []
          for (const conv of withTurns) {
            for (const t of conv.turns) {
              turns.push({ ...t, task_id: t.task_id || '' })
            }
          }
          allTurns.value = turns
          const active = withTurns.find((c: any) => c.status === 'active')
          convStatus.value = active ? 'active' : 'idle'
          activeTaskId.value = active?.current_task_id || ''
        }
      }

      if (allTurns.value.length > prevLen) scrollToBottom()
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
      // Don't clear history — just reload to get new task
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

async function loadSubagents() {
  loadingSubagents.value = true
  try {
    const r = await axios.get('/api/studio/subagents')
    if (r.data.status === 'ok') {
      availableSubagents.value = r.data.data || []
    }
  } catch (e: any) {
    console.warn('loadSubagents error:', e?.message)
  } finally {
    loadingSubagents.value = false
  }
}

function isBound(name: string): boolean {
  return members.value.some(m => m.name === name)
}

async function bindSubAgent(sa: { name: string; public_description: string }) {
  if (isBound(sa.name)) { toast('该 SubAgent 已绑定', 'warning'); return }
  addingMember.value = true
  try {
    const r = await axios.post('/api/studio/member', {
      name: sa.name,
      persona_prompt: sa.public_description || `SubAgent: ${sa.name}`,
      subagent_name: sa.name,
      public_description: sa.public_description,
    })
    if (r.data.status === 'ok') { toast(`已绑定 ${sa.name}`); await loadAll() }
    else toast(r.data.message || '绑定失败', 'error')
  } catch (e: any) { toast(e?.response?.data?.message || '绑定失败', 'error') }
  finally { addingMember.value = false }
}

async function resetConversation() {
  try {
    const r = await axios.post('/api/studio/reset')
    if (r.data.status === 'ok') {
      toast('已重置')
      allTurns.value = []
      activeTaskId.value = ''
      convStatus.value = 'idle'
      await loadAll()
    }
  } catch (e: any) { toast('重置失败', 'error') }
}

async function loadAll() {
  loading.value = true
  try { await Promise.all([loadStatus(), loadHistory()]); scrollToBottom() }
  finally { loading.value = false }
}

// ---------------------------------------------------------------------------
// Polling — 2s auto-refresh
// ---------------------------------------------------------------------------

watch(autoRefresh, v => v ? startPoll() : stopPoll())
watch(showAddMember, v => { if (v) loadSubagents() })

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

/* Chat card — fills viewport height */
.chat-card { height: calc(100vh - 180px); min-height: 500px; }

/* Scrollable message area */
.chat-messages { overflow-y: auto; scroll-behavior: smooth; }
.chat-messages::-webkit-scrollbar { width: 5px; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 5px; }

/* Timeline overrides for compact look */
.chat-messages :deep(.v-timeline) { padding-top: 0; }
.chat-messages :deep(.v-timeline-item__body) { padding-inline-start: 12px; }
.chat-messages :deep(.v-timeline-item) { padding-bottom: 8px; }

/* Task header */
.task-header-item { margin-bottom: 4px; }

/* Chat bubble base */
.chat-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.55;
  font-size: 0.85rem;
  display: inline-block;
  text-align: left;
  max-width: 100%;
  transition: background 0.15s;
}
.chat-bubble:hover { filter: brightness(0.97); }

.left-bubble { border-top-left-radius: 4px; }

/* Response text — scrollable when long */
.response-text { max-height: 300px; overflow-y: auto; }
.response-text::-webkit-scrollbar { width: 3px; }
.response-text::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.08); border-radius: 3px; }

/* Code blocks */
.code-block {
  background: #1e1e1e; color: #d4d4d4;
  font-family: 'Cascadia Code','Fira Code','Consolas',monospace;
  font-size: 0.8rem; line-height: 1.4; overflow-x: auto;
}

/* Centered delegation pill */
.delegation-pill { background: rgba(var(--v-theme-primary), 0.06); border: 1px solid rgba(var(--v-theme-primary), 0.12); }

/* Live indicator dot */
.live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #4caf50; display: inline-block;
  animation: pulse 1.5s ease-in-out infinite;
}
.live-dot-sm {
  width: 6px; height: 6px; border-radius: 50%;
  background: #4caf50; display: inline-block;
  margin-right: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(1.4); } }
</style>

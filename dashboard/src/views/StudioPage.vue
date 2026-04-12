<template>
  <div class="studio-page">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <div class="d-flex align-center gap-2 mb-1">
          <h2 class="text-h5 font-weight-bold">Studio 工作室</h2>
          <v-chip size="x-small" color="orange-darken-2" variant="tonal" label class="font-weight-bold">
            Beta
          </v-chip>
        </div>
        <div class="text-body-2 text-medium-emphasis">
          多成员 AI 协作工作台 · 实时追踪编码-审查闭环
        </div>
      </div>
      <div class="d-flex align-center gap-2">
        <v-btn
          variant="text"
          color="primary"
          prepend-icon="mdi-refresh"
          :loading="loading"
          @click="loadAll"
        >
          刷新
        </v-btn>
        <v-switch
          v-model="autoRefresh"
          label="自动刷新"
          color="primary"
          hide-details
          inset
          density="compact"
          class="mr-2"
        />
        <v-btn
          variant="flat"
          color="primary"
          prepend-icon="mdi-plus"
          @click="showAddMember = true"
        >
          添加成员
        </v-btn>
      </div>
    </div>

    <!-- Error banner -->
    <v-alert
      v-if="apiError"
      type="error"
      variant="tonal"
      class="mb-4 rounded-lg"
      density="compact"
      closable
      @click:close="apiError = ''"
    >
      {{ apiError }}
    </v-alert>

    <!-- Engine warning -->
    <v-alert
      v-if="!loading && !status.engineReady"
      type="warning"
      variant="tonal"
      class="mb-4 rounded-lg"
      density="compact"
      icon="mdi-alert-circle"
    >
      执行引擎未连接，请检查 claudecode 插件是否正常加载
    </v-alert>

    <!-- Main 3-column layout: 25% / 50% / 25% -->
    <v-row>
      <!-- Left: Members (25%) -->
      <v-col cols="12" md="3">
        <v-card class="rounded-lg border-thin fill-height" variant="flat" border>
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center gap-2">
              <v-icon icon="mdi-account-group" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">成员</span>
            </div>
            <v-chip size="x-small" variant="tonal" color="primary">
              {{ members.length }}
            </v-chip>
          </v-card-title>
          <v-divider />

          <!-- Loading skeleton -->
          <v-card-text v-if="loading && members.length === 0" class="pa-4">
            <v-skeleton-loader type="list-item@3" />
          </v-card-text>

          <v-card-text v-else class="pa-2">
            <v-list-item
              v-for="member in members"
              :key="member.name"
              :active="selectedMember === member.name"
              class="rounded-lg mb-1"
              @click="selectedMember = member.name"
            >
              <template #prepend>
                <v-avatar :color="getMemberColor(member.name)" size="32" class="mr-2">
                  <span class="text-white text-caption font-weight-bold">
                    {{ getMemberInitial(member) }}
                  </span>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2 font-weight-medium">
                {{ member.name }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption text-medium-emphasis text-truncate">
                {{ truncate(member.persona_prompt, 28) }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  icon="mdi-close-circle"
                  variant="text"
                  size="x-small"
                  color="grey"
                  @click.stop="removeMember(member.name)"
                />
              </template>
            </v-list-item>

            <div v-if="members.length === 0" class="text-center py-6 text-medium-emphasis">
              <v-icon icon="mdi-account-off" size="40" class="mb-2 opacity-50" />
              <div class="text-caption">暂无成员，点击上方添加</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Center: Collaboration Timeline (50%) -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg border-thin" variant="flat" border>
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center gap-2">
              <v-icon icon="mdi-forum" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="activeConv" size="x-small" :color="statusColor(activeConv.status)" variant="tonal">
                {{ statusLabel(activeConv.status) }}
              </v-chip>
            </div>
            <div class="d-flex align-center gap-1">
              <v-btn
                v-if="activeConv"
                icon="mdi-close-circle-outline"
                variant="text"
                size="small"
                color="error"
                @click="resetConversation"
              >
                <v-tooltip activator="parent" location="top">重置协作</v-tooltip>
              </v-btn>
            </div>
          </v-card-title>
          <v-divider />

          <div class="chat-log pa-4" ref="chatLogRef">
            <!-- Loading skeleton -->
            <div v-if="loading && !activeConv" class="pa-4">
              <v-skeleton-loader type="card@2" />
            </div>

            <!-- Empty state -->
            <div v-else-if="!activeConv || activeConv.turns.length === 0" class="text-center py-12 text-medium-emphasis">
              <v-icon icon="mdi-chat-processing-outline" size="64" class="mb-4 opacity-30" />
              <div class="text-body-1">暂无协作记录</div>
              <div class="text-caption mt-1">通过 /studio chat 命令启动协作</div>
            </div>

            <!-- Timeline -->
            <v-timeline v-else side="end" density="compact" align="start">
              <v-timeline-item
                v-for="(turn, idx) in activeConv.turns"
                :key="idx"
                :dot-color="getMemberColor(turn.to_member)"
                :icon="turn.auto_delegated ? 'mdi-link-variant' : 'mdi-circle-small'"
                size="small"
                class="turn-item"
              >
                <!-- Turn header -->
                <div class="d-flex align-center gap-2 mb-1">
                  <span class="text-subtitle-2 font-weight-bold">{{ turn.to_member }}</span>
                  <v-chip v-if="turn.auto_delegated" size="x-small" variant="tonal" color="info" label>
                    自动委托
                  </v-chip>
                  <span class="text-caption text-medium-emphasis ml-auto">
                    R{{ idx + 1 }} · {{ turn.from_member }}
                  </span>
                </div>

                <!-- Task bubble -->
                <v-card class="mb-2 rounded-lg" variant="outlined" color="blue-grey-lighten-5">
                  <v-card-text class="pa-2">
                    <div class="text-caption font-weight-bold text-primary">任务</div>
                    <div class="text-body-2">{{ turn.message }}</div>
                  </v-card-text>
                </v-card>

                <!-- Response card -->
                <v-card class="rounded-lg" variant="outlined">
                  <v-card-text class="pa-3">
                    <div class="text-caption font-weight-bold text-medium-emphasis mb-1">回复</div>
                    <div class="response-content">
                      <!-- Check if response contains code/diff -->
                      <template v-if="hasCodeBlock(turn.response)">
                        <div
                          v-for="(seg, si) in parseResponse(turn.response)"
                          :key="si"
                        >
                          <pre
                            v-if="seg.type === 'code'"
                            class="code-block rounded pa-3 mb-2"
                          ><code>{{ seg.content }}</code></pre>
                          <span v-else>{{ seg.content }}</span>
                        </div>
                      </template>
                      <template v-else>{{ turn.response }}</template>
                    </div>
                  </v-card-text>
                </v-card>

                <!-- Delegation arrow -->
                <div v-if="turn.delegated_to" class="d-flex align-center gap-1 mt-2 ml-2">
                  <v-icon icon="mdi-arrow-right-bottom" size="small" color="primary" />
                  <span class="text-caption text-primary font-weight-medium">
                    委托 → {{ turn.delegated_to }}
                  </span>
                </div>
              </v-timeline-item>
            </v-timeline>
          </div>
        </v-card>
      </v-col>

      <!-- Right: Status & Context (25%) -->
      <v-col cols="12" md="3">
        <div class="d-flex flex-column gap-4">
          <!-- Task Status Card -->
          <v-card class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center gap-2 py-3 px-4">
              <v-icon icon="mdi-information-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">任务状态</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column gap-3">
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">执行引擎</span>
                  <v-chip :color="status.engineReady ? 'success' : 'error'" size="small" variant="tonal">
                    {{ status.engineReady ? '已连接' : '未连接' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">自动委托</span>
                  <v-chip :color="status.autoDelegate ? 'success' : 'grey'" size="small" variant="tonal">
                    {{ status.autoDelegate ? '开启' : '关闭' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">智能停止</span>
                  <v-chip :color="status.autoStop ? 'success' : 'grey'" size="small" variant="tonal">
                    {{ status.autoStop ? '开启' : '关闭' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">轮次上限</span>
                  <span class="text-body-2 font-weight-medium">{{ status.maxRounds }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">活跃会话</span>
                  <span class="text-body-2 font-weight-medium">{{ status.activeCount }} / {{ status.totalCount }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Context Memory Card -->
          <v-card v-if="activeConv" class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center gap-2 py-3 px-4">
              <v-icon icon="mdi-brain" size="small" color="deep-purple" />
              <span class="text-subtitle-2 font-weight-bold">上下文记忆</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column gap-3">
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近修改</div>
                  <v-chip
                    v-if="activeConv.last_modified_by"
                    size="small"
                    :color="getMemberColor(activeConv.last_modified_by)"
                    variant="tonal"
                  >
                    {{ activeConv.last_modified_by }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近审查</div>
                  <v-chip
                    v-if="activeConv.last_review_by"
                    size="small"
                    :color="getMemberColor(activeConv.last_review_by)"
                    variant="tonal"
                  >
                    {{ activeConv.last_review_by }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">协作进度</div>
                  <div class="d-flex align-center gap-2">
                    <v-progress-linear
                      :model-value="progressPercent"
                      :color="progressColor"
                      height="6"
                      rounded
                      class="flex-grow-1"
                    />
                    <span class="text-caption font-weight-medium">
                      {{ activeConv.turns.length }}/{{ activeConv.max_rounds }}
                    </span>
                  </div>
                </div>
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">自动委托次数</div>
                  <span class="text-body-2 font-weight-medium">
                    {{ activeConv.auto_delegate_count || 0 }}
                  </span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Quick Actions Card -->
          <v-card class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center gap-2 py-3 px-4">
              <v-icon icon="mdi-lightning-bolt" size="small" color="amber" />
              <span class="text-subtitle-2 font-weight-bold">快捷操作</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column gap-2">
                <v-btn variant="outlined" block size="small" prepend-icon="mdi-refresh" @click="loadAll">
                  刷新状态
                </v-btn>
                <v-btn variant="outlined" block size="small" prepend-icon="mdi-history" @click="loadHistory">
                  查看完整历史
                </v-btn>
                <v-btn
                  variant="outlined"
                  block
                  size="small"
                  color="error"
                  prepend-icon="mdi-delete-outline"
                  :disabled="!activeConv"
                  @click="resetConversation"
                >
                  重置当前协作
                </v-btn>
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
          <span class="text-h6">添加工作室成员</span>
          <v-btn icon="mdi-close" variant="text" @click="showAddMember = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-text-field
            v-model="newMember.name"
            label="成员名称"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-account"
            class="mb-4"
          />
          <v-textarea
            v-model="newMember.persona"
            label="人格提示词"
            variant="outlined"
            density="comfortable"
            auto-grow
            rows="3"
            prepend-inner-icon="mdi-text"
            placeholder="描述该成员的专业能力和风格..."
          />
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showAddMember = false">取消</v-btn>
          <v-btn variant="flat" color="primary" :loading="addingMember" @click="addMember">
            添加
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="top">
      {{ snackbar.message }}
      <template #actions>
        <v-btn variant="text" @click="snackbar.show = false">关闭</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Member = {
  name: string
  emoji: string
  persona_prompt: string
  created_at: number
}

type Turn = {
  from_member: string
  to_member: string
  message: string
  response: string
  delegated_to: string | null
  auto_delegated: boolean
  timestamp: number
}

type Conversation = {
  id: string
  turns: Turn[]
  initial_member: string | null
  status: 'idle' | 'active' | 'completed' | 'timeout' | 'error'
  max_rounds: number
  created_at: number
  updated_at: number
  last_modified_by: string | null
  last_review_by: string | null
  last_action_type: string | null
  auto_delegate_count: number
}

type StudioStatus = {
  engineReady: boolean
  autoDelegate: boolean
  autoStop: boolean
  maxRounds: number
  activeCount: number
  totalCount: number
  memberCount: number
  persistMembers: boolean
  autoReview: boolean
}

type ResponseSegment = {
  type: 'text' | 'code'
  content: string
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const loading = ref(false)
const addingMember = ref(false)
const autoRefresh = ref(true)
const showAddMember = ref(false)
const selectedMember = ref<string | null>(null)
const chatLogRef = ref<HTMLElement | null>(null)
const apiError = ref('')

const snackbar = ref({ show: false, message: '', color: 'success' })

const status = ref<StudioStatus>({
  engineReady: false,
  autoDelegate: false,
  autoStop: false,
  maxRounds: 10,
  activeCount: 0,
  totalCount: 0,
  memberCount: 0,
  persistMembers: false,
  autoReview: false,
})

const members = ref<Member[]>([])
const conversations = ref<Conversation[]>([])
const activeConv = ref<Conversation | null>(null)

const newMember = ref({ name: '', persona: '' })

let refreshTimer: ReturnType<typeof setInterval> | null = null

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const progressPercent = computed(() => {
  if (!activeConv.value) return 0
  return (activeConv.value.turns.length / activeConv.value.max_rounds) * 100
})

const progressColor = computed(() => {
  if (!activeConv.value) return 'primary'
  const ratio = activeConv.value.turns.length / activeConv.value.max_rounds
  if (ratio >= 1) return 'error'
  if (ratio >= 0.7) return 'warning'
  return 'primary'
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const memberColors: Record<string, string> = {}
const colorPalette = [
  'deep-purple', 'blue', 'teal', 'indigo', 'cyan',
  'pink', 'orange', 'green', 'brown', 'blue-grey',
]

function getMemberColor(name: string): string {
  if (!memberColors[name]) {
    const idx = Object.keys(memberColors).length % colorPalette.length
    memberColors[name] = colorPalette[idx]
  }
  return memberColors[name]
}

function getMemberInitial(member: Member): string {
  if (member.emoji && member.emoji !== '🤖') {
    return member.emoji
  }
  return member.name[0]
}

function truncate(text: string, max: number): string {
  if (!text) return '暂无设定'
  return text.length > max ? text.substring(0, max) + '...' : text
}

function statusColor(s: string): string {
  const map: Record<string, string> = {
    active: 'info', completed: 'success', timeout: 'warning', error: 'error', idle: 'grey',
  }
  return map[s] || 'grey'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    active: '进行中', completed: '已完成', timeout: '超时', error: '错误', idle: '空闲',
  }
  return map[s] || s
}

function toast(message: string, color: 'success' | 'error' | 'warning' = 'success') {
  snackbar.value = { show: true, message, color }
}

function scrollToBottom() {
  setTimeout(() => {
    if (chatLogRef.value) {
      chatLogRef.value.scrollTop = chatLogRef.value.scrollHeight
    }
  }, 100)
}

// ---------------------------------------------------------------------------
// Response parsing (code/diff detection)
// ---------------------------------------------------------------------------

const codeBlockRe = /```[\w]*\n([\s\S]*?)```/g

function hasCodeBlock(text: string): boolean {
  return codeBlockRe.test(text)
}

function parseResponse(text: string): ResponseSegment[] {
  const segments: ResponseSegment[] = []
  let lastIndex = 0
  // Reset regex state
  codeBlockRe.lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = codeBlockRe.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'code', content: match[1].trim() })
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }
  return segments.length > 0 ? segments : [{ type: 'text', content: text }]
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function loadStatus() {
  try {
    const res = await axios.get('/api/studio/status')
    if (res.data.status === 'ok') {
      const d = res.data.data
      status.value = {
        engineReady: !!d.engine_ok,
        autoDelegate: d.auto_delegate !== false,
        autoStop: d.auto_stop !== false,
        maxRounds: d.max_rounds || 10,
        activeCount: d.active_count || 0,
        totalCount: d.total_count || 0,
        memberCount: d.member_count || 0,
        persistMembers: d.persist_members !== false,
        autoReview: d.auto_review === true,
      }
      if (d.members && typeof d.members === 'object') {
        members.value = Object.entries(d.members).map(([name, info]: [string, any]) => ({
          name,
          emoji: info.emoji || '🤖',
          persona_prompt: info.persona_prompt || '',
          created_at: info.created_at || 0,
        }))
      }
      apiError.value = ''
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      apiError.value = 'Studio API 未就绪，请确认插件已注册 /api/studio/* 路由'
    } else {
      console.warn('Studio status API error:', e?.message)
    }
  }
}

async function loadHistory() {
  try {
    const res = await axios.get('/api/studio/history')
    if (res.data.status === 'ok') {
      const data = res.data.data
      if (data && typeof data === 'object') {
        conversations.value = Object.values(data) as Conversation[]
        const active = conversations.value
          .filter((c) => c.turns && c.turns.length > 0)
          .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
        const prevTurns = activeConv.value?.turns.length ?? 0
        activeConv.value = active[0] || null
        if (activeConv.value && activeConv.value.turns.length > prevTurns) {
          scrollToBottom()
        }
      }
    }
  } catch (e: any) {
    console.warn('Studio history API error:', e?.message)
  }
}

async function addMember() {
  if (!newMember.value.name.trim()) {
    toast('请输入成员名称', 'warning')
    return
  }
  if (!newMember.value.persona.trim()) {
    toast('请输入人格提示词', 'warning')
    return
  }
  addingMember.value = true
  try {
    const res = await axios.post('/api/studio/member', {
      name: newMember.value.name.trim(),
      persona_prompt: newMember.value.persona.trim(),
    })
    if (res.data.status === 'ok') {
      toast('成员添加成功')
      showAddMember.value = false
      newMember.value = { name: '', persona: '' }
      await loadAll()
    } else {
      toast(res.data.message || '添加失败', 'error')
    }
  } catch (e: any) {
    toast(e?.response?.data?.message || '添加失败', 'error')
  } finally {
    addingMember.value = false
  }
}

async function resetConversation() {
  try {
    const res = await axios.post('/api/studio/reset')
    if (res.data.status === 'ok') {
      toast('协作已重置')
      await loadAll()
    }
  } catch (e: any) {
    toast(e?.response?.data?.message || '重置失败', 'error')
  }
}

async function removeMember(name: string) {
  try {
    const res = await axios.delete('/api/studio/member', { data: { name } })
    if (res.data.status === 'ok') {
      toast(`已移除「${name}」`)
      await loadAll()
    }
  } catch (e: any) {
    toast(e?.response?.data?.message || '移除失败', 'error')
  }
}

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadStatus(), loadHistory()])
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// Auto-refresh (3 seconds)
// ---------------------------------------------------------------------------

watch(autoRefresh, (val) => {
  if (val) startAutoRefresh()
  else stopAutoRefresh()
})

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    loadStatus()
    loadHistory()
  }, 3000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  loadAll()
  if (autoRefresh.value) startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.studio-page {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.gap-2 { gap: 8px; }

.chat-log {
  height: 560px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-log::-webkit-scrollbar {
  width: 4px;
}

.chat-log::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}

.turn-item {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.response-content {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
  font-size: 0.85rem;
  line-height: 1.5;
}

.response-content::-webkit-scrollbar {
  width: 3px;
}

.response-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.4;
  overflow-x: auto;
}
</style>

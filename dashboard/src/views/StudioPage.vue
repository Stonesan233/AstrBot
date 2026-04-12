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

    <!-- Engine Status Banner -->
    <v-alert
      v-if="!status.engineReady"
      type="warning"
      variant="tonal"
      class="mb-4 rounded-lg"
      density="compact"
      icon="mdi-alert-circle"
    >
      执行引擎未连接，请检查 claudecode 插件是否正常加载
    </v-alert>

    <!-- Main 3-column layout -->
    <v-row>
      <!-- Left: Members -->
      <v-col cols="12" md="3" lg="2">
        <v-card class="rounded-lg border-thin" variant="flat" border height="100%">
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
          <v-card-text class="pa-2">
            <div v-for="member in members" :key="member.name">
              <v-list-item
                :active="selectedMember === member.name"
                class="rounded-lg mb-1"
                @click="selectedMember = member.name"
              >
                <template #prepend>
                  <v-avatar :color="getMemberColor(member.name)" size="32" class="mr-2">
                    <span class="text-white text-caption font-weight-bold">
                      {{ member.emoji || member.name[0] }}
                    </span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2 font-weight-medium">
                  {{ member.name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption text-medium-emphasis text-truncate">
                  {{ member.persona_prompt?.substring(0, 30) || '暂无设定' }}...
                </v-list-item-subtitle>
              </v-list-item>
            </div>
            <div v-if="members.length === 0" class="text-center py-6 text-medium-emphasis">
              <v-icon icon="mdi-account-off" size="40" class="mb-2 opacity-50" />
              <div class="text-caption">暂无成员</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Center: Collaboration Log -->
      <v-col cols="12" md="5" lg="6">
        <v-card class="rounded-lg border-thin" variant="flat" border>
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center gap-2">
              <v-icon icon="mdi-forum" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="activeConv" size="x-small" :color="statusColor(activeConv.status)" variant="tonal">
                {{ statusLabel(activeConv.status) }}
              </v-chip>
            </div>
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
          </v-card-title>
          <v-divider />

          <!-- Chat log area -->
          <div class="chat-log pa-4" ref="chatLogRef">
            <div v-if="!activeConv || activeConv.turns.length === 0" class="text-center py-12 text-medium-emphasis">
              <v-icon icon="mdi-chat-processing-outline" size="64" class="mb-4 opacity-30" />
              <div class="text-body-1">暂无协作记录</div>
              <div class="text-caption mt-1">通过 /studio chat 命令启动协作</div>
            </div>

            <template v-else>
              <div
                v-for="(turn, idx) in activeConv.turns"
                :key="idx"
                class="turn-item mb-4"
              >
                <!-- Turn header -->
                <div class="d-flex align-center gap-2 mb-2">
                  <v-avatar :color="getMemberColor(turn.to_member)" size="24">
                    <span class="text-white text-caption">
                      {{ turn.to_member?.[0] || '?' }}
                    </span>
                  </v-avatar>
                  <span class="text-subtitle-2 font-weight-bold">{{ turn.to_member }}</span>
                  <v-chip v-if="turn.auto_delegated" size="x-small" variant="tonal" color="info" label>
                    自动委托
                  </v-chip>
                  <span class="text-caption text-medium-emphasis ml-auto">
                    第 {{ idx + 1 }} 轮 · 来自 {{ turn.from_member }}
                  </span>
                </div>

                <!-- Task -->
                <div class="turn-task pa-2 rounded bg-blue-grey-lighten-5 mb-2">
                  <div class="text-caption font-weight-bold text-primary mb-1">任务</div>
                  <div class="text-body-2">{{ turn.message }}</div>
                </div>

                <!-- Response -->
                <div class="turn-response pa-3 rounded-lg" style="background: rgb(var(--v-theme-surface))">
                  <div class="text-caption font-weight-bold text-medium-emphasis mb-1">回复</div>
                  <div class="text-body-2 response-content">{{ turn.response }}</div>
                </div>

                <!-- Delegation indicator -->
                <div v-if="turn.delegated_to" class="d-flex align-center gap-1 mt-2 ml-4">
                  <v-icon icon="mdi-arrow-right-bottom" size="small" color="primary" />
                  <span class="text-caption text-primary font-weight-medium">
                    委托 → {{ turn.delegated_to }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </v-card>
      </v-col>

      <!-- Right: Status & Context -->
      <v-col cols="12" md="4" lg="4">
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
                <div class="d-flex justify-space-between">
                  <span class="text-body-2 text-medium-emphasis">执行引擎</span>
                  <v-chip :color="status.engineReady ? 'success' : 'error'" size="small" variant="tonal">
                    {{ status.engineReady ? '已连接' : '未连接' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-body-2 text-medium-emphasis">自动委托</span>
                  <v-chip :color="status.autoDelegate ? 'success' : 'grey'" size="small" variant="tonal">
                    {{ status.autoDelegate ? '已开启' : '已关闭' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-body-2 text-medium-emphasis">智能停止</span>
                  <v-chip :color="status.autoStop ? 'success' : 'grey'" size="small" variant="tonal">
                    {{ status.autoStop ? '已开启' : '已关闭' }}
                  </v-chip>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-body-2 text-medium-emphasis">轮次上限</span>
                  <span class="text-body-2 font-weight-medium">{{ status.maxRounds }}</span>
                </div>
                <div class="d-flex justify-space-between">
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
                  <div class="text-caption text-medium-emphasis mb-1">协作轮次</div>
                  <div class="d-flex align-center gap-2">
                    <v-progress-linear
                      :model-value="(activeConv.turns.length / activeConv.max_rounds) * 100"
                      :color="activeConv.turns.length >= activeConv.max_rounds ? 'error' : 'primary'"
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
                <v-btn
                  variant="outlined"
                  block
                  size="small"
                  prepend-icon="mdi-refresh"
                  @click="loadAll"
                >
                  刷新状态
                </v-btn>
                <v-btn
                  variant="outlined"
                  block
                  size="small"
                  prepend-icon="mdi-history"
                  @click="loadHistory"
                >
                  查看完整历史
                </v-btn>
                <v-btn
                  variant="outlined"
                  block
                  size="small"
                  color="error"
                  prepend-icon="mdi-delete-outline"
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

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const loading = ref(false)
const addingMember = ref(false)
const autoRefresh = ref(true)
const showAddMember = ref(false)
const selectedMember = ref<string | null>(null)
const chatLogRef = ref<HTMLElement | null>(null)

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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
      // Parse members from status text
      if (d.members && typeof d.members === 'object') {
        members.value = Object.entries(d.members).map(([name, info]: [string, any]) => ({
          name,
          emoji: info.emoji || '🤖',
          persona_prompt: info.persona_prompt || '',
          created_at: info.created_at || 0,
        }))
      }
    }
  } catch (e: any) {
    // Studio plugin might not expose API yet, fail silently
    console.warn('Studio status API unavailable:', e?.message)
  }
}

async function loadHistory() {
  try {
    const res = await axios.get('/api/studio/history')
    if (res.data.status === 'ok') {
      const data = res.data.data
      if (data && typeof data === 'object') {
        conversations.value = Object.values(data) as Conversation[]
        // Pick the most recently updated conversation
        const active = conversations.value
          .filter((c) => c.turns && c.turns.length > 0)
          .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
        activeConv.value = active[0] || null
        scrollToBottom()
      }
    }
  } catch (e: any) {
    console.warn('Studio history API unavailable:', e?.message)
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
      toast(`已移除成员「${name}」`)
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
// Auto-refresh
// ---------------------------------------------------------------------------

watch(autoRefresh, (val) => {
  if (val) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    loadStatus()
    loadHistory()
  }, 5000)
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
  if (autoRefresh.value) {
    startAutoRefresh()
  }
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

.gap-2 {
  gap: 8px;
}

.gap-4 {
  gap: 16px;
}

.chat-log {
  height: 520px;
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

.turn-response {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.response-content {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
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
</style>

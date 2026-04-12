<template>
  <div class="studio-page">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <div class="d-flex align-center ga-2 mb-1">
          <v-icon icon="mdi-account-group" color="primary" />
          <h2 class="text-h5 font-weight-bold">Studio 工作室</h2>
          <v-chip size="x-small" color="orange-darken-2" variant="tonal" label class="font-weight-bold">
            Beta
          </v-chip>
        </div>
        <div class="text-body-2 text-medium-emphasis">
          多成员 AI 协作工作台 · 实时追踪编码-审查闭环
        </div>
      </div>
      <div class="d-flex align-center ga-3">
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

    <!-- Main 3-column layout -->
    <v-row>
      <!-- ======== Left: Members (25%) ======== -->
      <v-col cols="12" md="3">
        <v-card class="rounded-lg border-thin fill-height" variant="flat" border>
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-account-group" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">成员</span>
            </div>
            <v-chip size="x-small" variant="tonal" color="primary">
              {{ members.length }}
            </v-chip>
          </v-card-title>
          <v-divider />

          <!-- Loading -->
          <v-card-text v-if="loading && members.length === 0" class="pa-4">
            <v-skeleton-loader type="list-item@3" />
          </v-card-text>

          <v-card-text v-else class="pa-2">
            <v-list-item
              v-for="member in members"
              :key="member.name"
              :active="selectedMember === member.name"
              class="rounded-lg mb-1 member-item"
              @click="selectedMember = member.name"
            >
              <template #prepend>
                <div class="position-relative mr-3">
                  <v-avatar :color="getMemberColor(member.name)" size="36">
                    <span class="text-white text-body-2 font-weight-bold">
                      {{ getMemberInitial(member) }}
                    </span>
                  </v-avatar>
                  <!-- Online indicator -->
                  <v-badge
                    :color="isMemberActive(member.name) ? 'success' : 'grey'"
                    dot
                    location="bottom end"
                    floating
                    :offset-x="2"
                    :offset-y="2"
                  />
                </div>
              </template>
              <v-list-item-title class="text-body-2 font-weight-medium">
                {{ member.name }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption text-medium-emphasis text-truncate" style="max-width: 160px">
                {{ truncate(member.persona_prompt, 32) }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  icon="mdi-close-circle-outline"
                  variant="text"
                  size="x-small"
                  color="grey"
                  class="opacity-0 member-remove-btn"
                  @click.stop="removeMember(member.name)"
                />
              </template>
            </v-list-item>

            <div v-if="members.length === 0" class="text-center py-8 text-medium-emphasis">
              <v-icon icon="mdi-account-off-outline" size="48" class="mb-2 opacity-40" />
              <div class="text-caption">暂无成员，点击上方添加</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ======== Center: Collaboration Timeline (50%) ======== -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg border-thin" variant="flat" border>
          <!-- Title bar with live indicator -->
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-forum-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="activeConv" size="x-small" :color="statusColor(activeConv.status)" variant="tonal">
                {{ statusLabel(activeConv.status) }}
              </v-chip>
              <!-- Live pulse when active -->
              <div v-if="activeConv?.status === 'active'" class="live-dot ml-1" />
            </div>
            <div class="d-flex align-center ga-1">
              <span v-if="activeConv" class="text-caption text-medium-emphasis">
                {{ activeConv.turns.length }} 轮
              </span>
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

          <!-- Scrollable chat log -->
          <div class="chat-log pa-4" ref="chatLogRef">
            <!-- Loading -->
            <div v-if="loading && !activeConv" class="pa-4">
              <v-skeleton-loader type="card@3" />
            </div>

            <!-- Empty state -->
            <div v-else-if="!activeConv || activeConv.turns.length === 0" class="text-center py-16 text-medium-emphasis">
              <v-icon icon="mdi-chat-processing-outline" size="72" class="mb-4 opacity-20" />
              <div class="text-body-1 mb-1">暂无协作记录</div>
              <div class="text-caption">通过 /studio chat 命令启动协作</div>
            </div>

            <!-- Timeline -->
            <div v-else>
              <!-- Delegation flow overview bar -->
              <div v-if="activeConv.turns.length > 1" class="delegation-flow-bar mb-4 pa-3 rounded-lg">
                <div class="text-caption text-medium-emphasis mb-2 font-weight-bold">委托链路</div>
                <div class="d-flex align-center flex-wrap ga-1">
                  <template v-for="(turn, idx) in activeConv.turns" :key="idx">
                    <v-chip
                      size="x-small"
                      :color="getMemberColor(turn.to_member)"
                      variant="tonal"
                      class="font-weight-bold"
                    >
                      {{ turn.to_member }}
                    </v-chip>
                    <v-icon
                      v-if="idx < activeConv.turns.length - 1"
                      icon="mdi-arrow-right"
                      size="x-small"
                      :color="activeConv.turns[idx + 1]?.auto_delegated ? 'orange' : 'primary'"
                    />
                  </template>
                </div>
              </div>

              <v-timeline side="end" density="compact" align="start">
                <v-timeline-item
                  v-for="(turn, idx) in activeConv.turns"
                  :key="idx"
                  :dot-color="getMemberColor(turn.to_member)"
                  size="small"
                  class="turn-item"
                >
                  <template #icon>
                    <v-icon
                      :icon="turn.auto_delegated ? 'mdi-auto-fix' : 'mdi-circle-small'"
                      :color="turn.auto_delegated ? 'orange' : undefined"
                      size="small"
                    />
                  </template>

                  <!-- Turn header -->
                  <div class="d-flex align-center ga-2 mb-2">
                    <v-avatar :color="getMemberColor(turn.to_member)" size="24" class="mr-1">
                      <span class="text-white text-overline font-weight-bold" style="font-size: 10px">
                        {{ turn.to_member[0] }}
                      </span>
                    </v-avatar>
                    <span class="text-subtitle-2 font-weight-bold">{{ turn.to_member }}</span>
                    <v-chip v-if="turn.auto_delegated" size="x-small" variant="tonal" color="orange" label>
                      <v-icon icon="mdi-auto-fix" size="x-small" start />
                      自动委托
                    </v-chip>
                    <span class="text-caption text-medium-emphasis ml-auto">
                      R{{ idx + 1 }}
                    </span>
                    <span class="text-caption text-medium-emphasis">
                      来自 {{ turn.from_member }}
                    </span>
                  </div>

                  <!-- Task bubble -->
                  <v-card class="mb-2 rounded-lg task-bubble" variant="outlined" color="blue-grey-lighten-5">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center ga-1 mb-1">
                        <v-icon icon="mdi-clipboard-text-outline" size="x-small" color="primary" />
                        <span class="text-caption font-weight-bold text-primary">任务</span>
                      </div>
                      <div class="text-body-2">{{ turn.message }}</div>
                    </v-card-text>
                  </v-card>

                  <!-- Response card -->
                  <v-card class="rounded-lg response-card" variant="outlined">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center ga-1 mb-2">
                        <v-icon icon="mdi-reply-text-outline" size="x-small" color="medium-emphasis" />
                        <span class="text-caption font-weight-bold text-medium-emphasis">回复</span>
                        <v-spacer />
                        <v-btn
                          icon="mdi-content-copy"
                          variant="text"
                          size="x-small"
                          color="grey"
                          @click="copyText(turn.response)"
                        >
                          <v-tooltip activator="parent" location="top">复制</v-tooltip>
                        </v-btn>
                      </div>
                      <div class="response-content">
                        <template v-if="hasCodeBlock(turn.response)">
                          <div
                            v-for="(seg, si) in parseResponse(turn.response)"
                            :key="si"
                          >
                            <pre
                              v-if="seg.type === 'code'"
                              class="code-block rounded pa-3 mb-2"
                            ><code>{{ seg.content }}</code></pre>
                            <span v-else class="text-segment">{{ seg.content }}</span>
                          </div>
                        </template>
                        <template v-else>{{ turn.response }}</template>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- Delegation arrow with highlight -->
                  <div v-if="turn.delegated_to" class="delegation-arrow mt-2 ml-2 pa-2 rounded-lg">
                    <div class="d-flex align-center ga-2">
                      <v-icon
                        :icon="turn.auto_delegated ? 'mdi-swap-horizontal-bold' : 'mdi-arrow-right-bottom'"
                        size="small"
                        :color="turn.auto_delegated ? 'orange' : 'primary'"
                      />
                      <v-chip size="x-small" :color="getMemberColor(turn.to_member)" variant="tonal">
                        {{ turn.to_member }}
                      </v-chip>
                      <v-icon icon="mdi-arrow-right" size="x-small" color="primary" />
                      <v-chip size="x-small" :color="getMemberColor(turn.delegated_to)" variant="tonal">
                        {{ turn.delegated_to }}
                      </v-chip>
                      <span v-if="turn.auto_delegated" class="text-caption text-orange font-weight-medium ml-1">
                        自动
                      </span>
                    </div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- ======== Right: Status & Context (25%) ======== -->
      <v-col cols="12" md="3">
        <div class="d-flex flex-column ga-4">
          <!-- Task Status Card -->
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
                  <v-chip :color="status.engineReady ? 'success' : 'error'" size="small" variant="tonal">
                    <v-icon :icon="status.engineReady ? 'mdi-check-circle' : 'mdi-close-circle'" start size="x-small" />
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
                  <span class="text-body-2 font-weight-bold">{{ status.maxRounds }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">活跃会话</span>
                  <span class="text-body-2 font-weight-bold">{{ status.activeCount }} / {{ status.totalCount }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Context Memory Card -->
          <v-card v-if="activeConv" class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-brain" size="small" color="deep-purple" />
              <span class="text-subtitle-2 font-weight-bold">上下文记忆</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-3">
                <!-- Progress -->
                <div>
                  <div class="d-flex justify-space-between align-center mb-1">
                    <span class="text-caption text-medium-emphasis">协作进度</span>
                    <span class="text-caption font-weight-bold">
                      {{ activeConv.turns.length }} / {{ activeConv.max_rounds }} 轮
                    </span>
                  </div>
                  <v-progress-linear
                    :model-value="progressPercent"
                    :color="progressColor"
                    height="8"
                    rounded
                    class="mb-1"
                  />
                  <div class="text-right">
                    <span class="text-caption" :class="`text-${progressColor}`">
                      {{ progressPercent.toFixed(0) }}%
                    </span>
                  </div>
                </div>

                <v-divider />

                <!-- Last modification -->
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近修改</div>
                  <div v-if="activeConv.last_modified_by" class="d-flex align-center ga-2">
                    <v-avatar :color="getMemberColor(activeConv.last_modified_by)" size="20">
                      <span class="text-white" style="font-size: 10px">{{ activeConv.last_modified_by[0] }}</span>
                    </v-avatar>
                    <span class="text-body-2 font-weight-medium">{{ activeConv.last_modified_by }}</span>
                  </div>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>

                <!-- Last review -->
                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近审查</div>
                  <div v-if="activeConv.last_review_by" class="d-flex align-center ga-2">
                    <v-avatar :color="getMemberColor(activeConv.last_review_by)" size="20">
                      <span class="text-white" style="font-size: 10px">{{ activeConv.last_review_by[0] }}</span>
                    </v-avatar>
                    <span class="text-body-2 font-weight-medium">{{ activeConv.last_review_by }}</span>
                  </div>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>

                <!-- Last review summary -->
                <div v-if="lastReviewSummary">
                  <div class="text-caption text-medium-emphasis mb-1">审查意见摘要</div>
                  <v-card variant="outlined" color="deep-purple-lighten-5" class="rounded-lg">
                    <v-card-text class="pa-2">
                      <div class="text-caption" style="max-height: 80px; overflow-y: auto">
                        {{ lastReviewSummary }}
                      </div>
                    </v-card-text>
                  </v-card>
                </div>

                <v-divider />

                <!-- Auto delegate stats -->
                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">自动委托次数</span>
                  <v-chip size="small" variant="tonal" color="orange">
                    {{ activeConv.auto_delegate_count || 0 }}
                  </v-chip>
                </div>

                <!-- Elapsed time -->
                <div v-if="activeConv.created_at" class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">已用时间</span>
                  <span class="text-body-2 font-weight-medium">{{ elapsedText }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Quick Actions Card -->
          <v-card class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-lightning-bolt" size="small" color="amber" />
              <span class="text-subtitle-2 font-weight-bold">快捷操作</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-2">
                <v-btn variant="outlined" block size="small" prepend-icon="mdi-refresh" @click="loadAll">
                  刷新状态
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
let elapsedTimer: ReturnType<typeof setInterval> | null = null

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

const elapsedText = computed(() => {
  if (!activeConv.value?.created_at) return '--'
  const start = activeConv.value.created_at * 1000
  const end = activeConv.value.status === 'active'
    ? Date.now()
    : (activeConv.value.updated_at || activeConv.value.created_at) * 1000
  const sec = Math.floor((end - start) / 1000)
  if (sec < 60) return `${sec}s`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
})

const lastReviewSummary = computed(() => {
  if (!activeConv.value) return null
  const reviewTurns = activeConv.value.turns.filter(
    (t) => t.response && t.response.length > 0 && isReviewResponse(t.response)
  )
  if (reviewTurns.length === 0) return null
  const last = reviewTurns[reviewTurns.length - 1]
  return truncate(last.response, 200)
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
  if (member.emoji && member.emoji !== '🤖') return member.emoji
  return member.name[0]
}

function truncate(text: string, max: number): string {
  if (!text) return '暂无设定'
  return text.length > max ? text.substring(0, max) + '...' : text
}

function isMemberActive(name: string): boolean {
  if (!activeConv.value) return false
  return activeConv.value.status === 'active' &&
    activeConv.value.turns.some((t) => t.to_member === name)
}

function isReviewResponse(text: string): boolean {
  const reviewKws = ['审查', '检查', '评审', '审核', 'review', '建议', '问题', '修改建议', '通过']
  const lower = text.toLowerCase()
  return reviewKws.some((kw) => lower.includes(kw))
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

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => toast('已复制')).catch(() => {})
}

function scrollToBottom() {
  setTimeout(() => {
    if (chatLogRef.value) {
      chatLogRef.value.scrollTop = chatLogRef.value.scrollHeight
    }
  }, 150)
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
// Auto-refresh (2 seconds)
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
  }, 2000)
  // Tick elapsed timer every second
  elapsedTimer = setInterval(() => {
    // Force reactivity tick for elapsedText computed
    if (activeConv.value?.status === 'active') {
      activeConv.value = { ...activeConv.value }
    }
  }, 1000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
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

/* Chat log scrollable area */
.chat-log {
  height: 600px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-log::-webkit-scrollbar {
  width: 5px;
}

.chat-log::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 5px;
}

/* Turn animation */
.turn-item {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Response content */
.response-content {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 260px;
  overflow-y: auto;
  font-size: 0.85rem;
  line-height: 1.6;
}

.response-content::-webkit-scrollbar {
  width: 3px;
}

.response-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

/* Code block */
.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.4;
  overflow-x: auto;
}

/* Delegation flow bar */
.delegation-flow-bar {
  background: rgb(var(--v-theme-surface-variant));
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* Delegation arrow highlight */
.delegation-arrow {
  background: linear-gradient(90deg, rgba(var(--v-theme-primary), 0.06), transparent);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

/* Live pulse dot */
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

/* Member item hover: show remove button */
.member-item .member-remove-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.member-item:hover .member-remove-btn {
  opacity: 1 !important;
}

/* Task bubble */
.task-bubble {
  border-left: 3px solid rgb(var(--v-theme-primary)) !important;
}

/* Response card */
.response-card {
  transition: box-shadow 0.2s;
}

.response-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
</style>

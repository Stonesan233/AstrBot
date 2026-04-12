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
        <v-btn variant="text" color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="loadAll">
          刷新
        </v-btn>
        <v-switch v-model="autoRefresh" label="自动刷新" color="primary" hide-details inset density="compact" />
        <v-btn variant="flat" color="primary" prepend-icon="mdi-plus" @click="showAddMember = true">
          添加成员
        </v-btn>
      </div>
    </div>

    <!-- Alerts -->
    <v-alert v-if="apiError" type="error" variant="tonal" class="mb-4 rounded-lg" density="compact" closable @click:close="apiError = ''">
      {{ apiError }}
    </v-alert>
    <v-alert v-if="!loading && !status.engineReady" type="warning" variant="tonal" class="mb-4 rounded-lg" density="compact" icon="mdi-alert-circle">
      执行引擎未连接，请检查 claudecode 插件是否正常加载
    </v-alert>

    <!-- 3-column layout -->
    <v-row>
      <!-- ========== Left: Members (3/12) ========== -->
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

          <v-card-text v-if="loading && members.length === 0" class="pa-4">
            <v-skeleton-loader type="list-item@3" />
          </v-card-text>

          <v-card-text v-else class="pa-2">
            <v-list-item
              v-for="member in members"
              :key="member.name"
              :active="selectedMember === member.name"
              class="rounded-lg mb-1 member-item"
              @click="selectMember(member.name)"
            >
              <template #prepend>
                <div class="position-relative mr-3">
                  <v-avatar :color="getMemberColor(member.name)" size="36">
                    <span class="text-white text-body-2 font-weight-bold">{{ member.name[0] }}</span>
                  </v-avatar>
                  <span
                    class="member-status-dot"
                    :class="isMemberActive(member.name) ? 'active' : 'idle'"
                  />
                </div>
              </template>
              <v-list-item-title class="text-body-2 font-weight-medium">{{ member.name }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption text-medium-emphasis text-truncate" style="max-width: 150px">
                {{ truncate(member.persona_prompt, 30) }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  icon="mdi-at"
                  variant="text"
                  size="x-small"
                  color="primary"
                  @click.stop="mentionMember(member.name)"
                >
                  <v-tooltip activator="parent" location="top">@{{ member.name }}</v-tooltip>
                </v-btn>
                <v-btn
                  icon="mdi-close-circle-outline"
                  variant="text"
                  size="x-small"
                  color="grey"
                  class="member-remove-btn"
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

      <!-- ========== Center: Chat Timeline (6/12) ========== -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg border-thin" variant="flat" border>
          <!-- Title bar -->
          <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
            <div class="d-flex align-center ga-2">
              <v-icon icon="mdi-forum-outline" size="small" color="primary" />
              <span class="text-subtitle-2 font-weight-bold">协作记录</span>
              <v-chip v-if="activeConv" size="x-small" :color="statusColor(activeConv.status)" variant="tonal">
                {{ statusLabel(activeConv.status) }}
              </v-chip>
              <span v-if="activeConv?.status === 'active'" class="live-dot" />
            </div>
            <div class="d-flex align-center ga-1">
              <span v-if="activeConv" class="text-caption text-medium-emphasis">
                {{ activeConv.turns.length }} / {{ activeConv.max_rounds }} 轮
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

          <!-- Chat log area -->
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
              <!-- Delegation flow chain -->
              <div v-if="activeConv.turns.length > 1" class="delegation-chain pa-3 rounded-lg mb-4">
                <div class="text-caption text-medium-emphasis mb-2 font-weight-bold">委托链路</div>
                <div class="d-flex align-center flex-wrap ga-1">
                  <template v-for="(turn, idx) in activeConv.turns" :key="idx">
                    <v-chip size="x-small" :color="getMemberColor(turn.to_member)" variant="tonal" class="font-weight-bold">
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

              <!-- Turn list -->
              <v-timeline side="end" density="compact" align="start">
                <v-timeline-item
                  v-for="(turn, idx) in activeConv.turns"
                  :key="turn.timestamp + '-' + idx"
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

                  <!-- Turn header: avatar + name + meta -->
                  <div class="d-flex align-center ga-2 mb-2">
                    <v-avatar :color="getMemberColor(turn.to_member)" size="28">
                      <span class="text-white text-overline font-weight-bold" style="font-size: 11px">
                        {{ turn.to_member[0] }}
                      </span>
                    </v-avatar>
                    <span class="text-subtitle-2 font-weight-bold">{{ turn.to_member }}</span>
                    <v-chip v-if="turn.auto_delegated" size="x-small" variant="tonal" color="orange" label>
                      <v-icon icon="mdi-auto-fix" size="x-small" start />自动
                    </v-chip>
                    <span class="text-caption text-medium-emphasis ml-auto">
                      {{ formatTime(turn.timestamp) }}
                    </span>
                    <span class="text-caption text-medium-emphasis">
                      R{{ idx + 1 }}
                    </span>
                  </div>

                  <!-- Task (message from delegator) -->
                  <v-card class="mb-2 rounded-lg task-bubble" variant="outlined">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center ga-1 mb-1">
                        <v-icon icon="mdi-clipboard-text-outline" size="x-small" color="primary" />
                        <span class="text-caption font-weight-bold text-primary">任务</span>
                        <span class="text-caption text-medium-emphasis ml-auto">来自 {{ turn.from_member }}</span>
                      </div>
                      <div class="text-body-2">{{ turn.message }}</div>
                    </v-card-text>
                  </v-card>

                  <!-- Response bubble -->
                  <v-card class="rounded-lg" variant="outlined">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center ga-1 mb-2">
                        <v-icon icon="mdi-reply-text-outline" size="x-small" color="medium-emphasis" />
                        <span class="text-caption font-weight-bold text-medium-emphasis">回复</span>
                        <v-spacer />
                        <v-btn icon="mdi-content-copy" variant="text" size="x-small" color="grey" @click="copyText(turn.response)">
                          <v-tooltip activator="parent" location="top">复制</v-tooltip>
                        </v-btn>
                      </div>
                      <div class="response-content">
                        <template v-if="hasCodeBlock(turn.response)">
                          <div v-for="(seg, si) in parseResponse(turn.response)" :key="si">
                            <pre v-if="seg.type === 'code'" class="code-block rounded pa-3 mb-2"><code>{{ seg.content }}</code></pre>
                            <span v-else>{{ seg.content }}</span>
                          </div>
                        </template>
                        <template v-else>{{ turn.response }}</template>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- Delegation arrow: this member → next member -->
                  <div v-if="turn.delegated_to" class="delegation-arrow mt-3 pa-2 rounded-lg">
                    <div class="d-flex align-center ga-2">
                      <v-icon
                        :icon="turn.auto_delegated ? 'mdi-swap-horizontal-bold' : 'mdi-arrow-right-bold-circle'"
                        size="small"
                        :color="turn.auto_delegated ? 'orange' : 'primary'"
                      />
                      <v-chip size="x-small" :color="getMemberColor(turn.to_member)" variant="tonal">
                        {{ turn.to_member }}
                      </v-chip>
                      <v-icon icon="mdi-arrow-right" size="small" :color="turn.auto_delegated ? 'orange' : 'primary'" />
                      <v-chip size="x-small" :color="getMemberColor(turn.delegated_to)" variant="tonal">
                        {{ turn.delegated_to }}
                      </v-chip>
                      <span v-if="turn.auto_delegated" class="text-caption text-orange-darken-2 font-weight-bold ml-1">
                        自动委托
                      </span>
                    </div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </div>
          </div>

          <!-- Chat input bar -->
          <v-divider />
          <div class="pa-3">
            <div class="d-flex align-center ga-2">
              <v-chip
                v-if="chatTarget"
                size="small"
                :color="getMemberColor(chatTarget)"
                variant="tonal"
                closable
                class="flex-shrink-0"
                @click:close="chatTarget = ''"
              >
                @{{ chatTarget }}
              </v-chip>
              <v-text-field
                v-model="chatInput"
                placeholder="输入任务消息... (支持 @成员名)"
                variant="outlined"
                density="compact"
                hide-details
                :disabled="sendingChat"
                @keydown.enter="sendChat"
              >
                <template #prepend-inner>
                  <v-icon icon="mdi-message-text-outline" size="small" color="medium-emphasis" />
                </template>
              </v-text-field>
              <v-btn
                variant="flat"
                color="primary"
                :loading="sendingChat"
                :disabled="!chatInput.trim() || activeConv?.status === 'active'"
                icon="mdi-send"
                size="small"
                @click="sendChat"
              >
                <v-tooltip activator="parent" location="top">发送</v-tooltip>
              </v-btn>
            </div>
            <div v-if="activeConv?.status === 'active'" class="text-caption text-info mt-2 d-flex align-center ga-1">
              <span class="live-dot" style="width:6px;height:6px" />
              协作进行中，新消息将在完成后发送...
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- ========== Right: Status (3/12) ========== -->
      <v-col cols="12" md="3">
        <div class="d-flex flex-column ga-4">
          <!-- Engine status -->
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

          <!-- Context memory -->
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
                    <span class="text-caption font-weight-bold">{{ activeConv.turns.length }} / {{ activeConv.max_rounds }}</span>
                  </div>
                  <v-progress-linear :model-value="progressPercent" :color="progressColor" height="8" rounded />
                </div>

                <v-divider />

                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近修改</div>
                  <v-chip v-if="activeConv.last_modified_by" size="small" :color="getMemberColor(activeConv.last_modified_by)" variant="tonal">
                    {{ activeConv.last_modified_by }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>

                <div>
                  <div class="text-caption text-medium-emphasis mb-1">最近审查</div>
                  <v-chip v-if="activeConv.last_review_by" size="small" :color="getMemberColor(activeConv.last_review_by)" variant="tonal">
                    {{ activeConv.last_review_by }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">无</span>
                </div>

                <div v-if="lastReviewSnippet">
                  <div class="text-caption text-medium-emphasis mb-1">审查摘要</div>
                  <v-card variant="outlined" class="rounded-lg pa-2" color="deep-purple-lighten-5">
                    <div class="text-caption" style="max-height: 80px; overflow-y: auto">{{ lastReviewSnippet }}</div>
                  </v-card>
                </div>

                <v-divider />

                <div class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">自动委托次数</span>
                  <v-chip size="small" variant="tonal" color="orange">{{ activeConv.auto_delegate_count || 0 }}</v-chip>
                </div>

                <div v-if="activeConv.created_at" class="d-flex justify-space-between align-center">
                  <span class="text-body-2 text-medium-emphasis">已用时间</span>
                  <span class="text-body-2 font-weight-medium">{{ elapsedText }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Quick actions -->
          <v-card class="rounded-lg border-thin" variant="flat" border>
            <v-card-title class="d-flex align-center ga-2 py-3 px-4">
              <v-icon icon="mdi-lightning-bolt" size="small" color="amber" />
              <span class="text-subtitle-2 font-weight-bold">快捷操作</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-4">
              <div class="d-flex flex-column ga-2">
                <v-btn variant="outlined" block size="small" prepend-icon="mdi-refresh" @click="loadAll">刷新状态</v-btn>
                <v-btn variant="outlined" block size="small" color="error" prepend-icon="mdi-delete-outline" :disabled="!activeConv" @click="resetConversation">
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
          <v-text-field v-model="newMember.name" label="成员名称" variant="outlined" density="comfortable" prepend-inner-icon="mdi-account" class="mb-4" />
          <v-textarea v-model="newMember.persona" label="人格提示词" variant="outlined" density="comfortable" auto-grow rows="3" prepend-inner-icon="mdi-text" placeholder="描述该成员的专业能力和风格..." />
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showAddMember = false">取消</v-btn>
          <v-btn variant="flat" color="primary" :loading="addingMember" @click="addMember">添加</v-btn>
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
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
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
const snackbar = ref({ show: false, message: '', color: 'success' as string })
const nowTick = ref(Date.now())

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
const activeConv = ref<Conversation | null>(null)
const newMember = ref({ name: '', persona: '' })
const chatInput = ref('')
const chatTarget = ref('')
const sendingChat = ref(false)

let pollTimer: ReturnType<typeof setInterval> | null = null
let tickTimer: ReturnType<typeof setInterval> | null = null

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const progressPercent = computed(() => {
  if (!activeConv.value) return 0
  return Math.min((activeConv.value.turns.length / activeConv.value.max_rounds) * 100, 100)
})

const progressColor = computed(() => {
  if (!activeConv.value) return 'primary'
  const r = activeConv.value.turns.length / activeConv.value.max_rounds
  if (r >= 1) return 'error'
  if (r >= 0.7) return 'warning'
  return 'primary'
})

const elapsedText = computed(() => {
  if (!activeConv.value?.created_at) return '--'
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _tick = nowTick.value // depends on tick so it recomputes
  const start = activeConv.value.created_at * 1000
  const end = activeConv.value.status === 'active'
    ? Date.now()
    : (activeConv.value.updated_at || activeConv.value.created_at) * 1000
  const sec = Math.max(0, Math.floor((end - start) / 1000))
  if (sec < 60) return `${sec}s`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
})

const lastReviewSnippet = computed(() => {
  if (!activeConv.value) return null
  const kws = ['审查', '检查', '评审', '审核', 'review', '建议', '问题', '通过']
  const rev = activeConv.value.turns
    .filter((t) => t.response && kws.some((k) => t.response.toLowerCase().includes(k)))
  if (rev.length === 0) return null
  const last = rev[rev.length - 1]
  return last.response.length > 200 ? last.response.substring(0, 200) + '...' : last.response
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const _colorMap: Record<string, string> = {}
const palette = ['deep-purple', 'blue', 'teal', 'indigo', 'cyan', 'pink', 'orange', 'green', 'brown', 'blue-grey']

function getMemberColor(name: string): string {
  if (!_colorMap[name]) {
    _colorMap[name] = palette[Object.keys(_colorMap).length % palette.length]
  }
  return _colorMap[name]
}

function truncate(text: string, max: number): string {
  if (!text) return '暂无设定'
  return text.length > max ? text.substring(0, max) + '...' : text
}

function isMemberActive(name: string): boolean {
  return activeConv.value?.status === 'active' &&
    activeConv.value.turns.some((t) => t.to_member === name)
}

function formatTime(ts: number): string {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function statusColor(s: string): string {
  return ({ active: 'info', completed: 'success', timeout: 'warning', error: 'error', idle: 'grey' } as Record<string, string>)[s] || 'grey'
}

function statusLabel(s: string): string {
  return ({ active: '进行中', completed: '已完成', timeout: '超时', error: '错误', idle: '空闲' } as Record<string, string>)[s] || s
}

function toast(message: string, color: string = 'success') {
  snackbar.value = { show: true, message, color }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => toast('已复制')).catch(() => {})
}

function selectMember(name: string) {
  selectedMember.value = name
}

function mentionMember(name: string) {
  chatTarget.value = name
  selectedMember.value = name
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatLogRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// ---------------------------------------------------------------------------
// Response parsing (code blocks)
// ---------------------------------------------------------------------------

const codeRe = /```[\w]*\n([\s\S]*?)```/g

function hasCodeBlock(text: string): boolean {
  return codeRe.test(text)
}

function parseResponse(text: string): ResponseSegment[] {
  const segs: ResponseSegment[] = []
  let last = 0
  codeRe.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = codeRe.exec(text)) !== null) {
    if (m.index > last) segs.push({ type: 'text', content: text.slice(last, m.index) })
    segs.push({ type: 'code', content: m[1].trim() })
    last = m.index + m[0].length
  }
  if (last < text.length) segs.push({ type: 'text', content: text.slice(last) })
  return segs.length > 0 ? segs : [{ type: 'text', content: text }]
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
    }
  }
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text) return
  if (activeConv.value?.status === 'active') {
    toast('协作正在进行中，请等待完成', 'warning')
    return
  }
  // Build message with @target prefix
  const fullMsg = chatTarget.value ? `@${chatTarget.value} ${text}` : text
  sendingChat.value = true
  try {
    const res = await axios.post('/api/studio/chat', { message: fullMsg })
    if (res.data.status === 'ok') {
      chatInput.value = ''
      toast('协作已启动')
      // Immediate poll to see the new conversation
      await loadHistory()
    } else {
      toast(res.data.message || '发送失败', 'error')
    }
  } catch (e: any) {
    toast(e?.response?.data?.message || '发送失败', 'error')
  } finally {
    sendingChat.value = false
  }
}

async function loadHistory() {
  try {
    const res = await axios.get('/api/studio/history')
    if (res.data.status === 'ok') {
      const data = res.data.data
      if (data && typeof data === 'object') {
        const all = Object.values(data) as Conversation[]
        const active = all
          .filter((c) => c.turns && c.turns.length > 0)
          .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
        const prevLen = activeConv.value?.turns.length ?? 0
        activeConv.value = active[0] || null
        // Auto scroll when new turns arrive
        if (activeConv.value && activeConv.value.turns.length > prevLen) {
          scrollToBottom()
        }
      }
    }
  } catch (e: any) {
    console.warn('Studio history error:', e?.message)
  }
}

async function addMember() {
  if (!newMember.value.name.trim()) { toast('请输入成员名称', 'warning'); return }
  if (!newMember.value.persona.trim()) { toast('请输入人格提示词', 'warning'); return }
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
      activeConv.value = null
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
// Polling (2s)
// ---------------------------------------------------------------------------

watch(autoRefresh, (v) => { v ? startPoll() : stopPoll() })

function startPoll() {
  stopPoll()
  pollTimer = setInterval(() => { loadStatus(); loadHistory() }, 2000)
  tickTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
}

function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  loadAll()
  if (autoRefresh.value) startPoll()
})

onUnmounted(() => {
  stopPoll()
})
</script>

<style scoped>
.studio-page {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.chat-log {
  height: 600px;
  overflow-y: auto;
  scroll-behavior: smooth;
}
.chat-log::-webkit-scrollbar { width: 5px; }
.chat-log::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 5px; }

.turn-item { animation: fadeIn 0.3s ease; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.response-content {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 280px;
  overflow-y: auto;
  font-size: 0.85rem;
  line-height: 1.6;
}
.response-content::-webkit-scrollbar { width: 3px; }
.response-content::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.4;
  overflow-x: auto;
}

.delegation-chain {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(0,0,0,0.06);
}

.delegation-arrow {
  background: linear-gradient(90deg, rgba(var(--v-theme-primary), 0.08), transparent);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  animation: pulse 1.5s ease-in-out infinite;
  display: inline-block;
}
@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%     { opacity: 0.4; transform: scale(1.4); }
}

.member-status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
}
.member-status-dot.active { background: #4caf50; }
.member-status-dot.idle   { background: #bdbdbd; }

.member-item .member-remove-btn { opacity: 0; transition: opacity 0.2s; }
.member-item:hover .member-remove-btn { opacity: 1 !important; }

.task-bubble { border-left: 3px solid rgb(var(--v-theme-primary)) !important; }
</style>

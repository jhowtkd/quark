<template>
  <div class="action-explorer">
    <!-- Header -->
    <div class="explorer-header">
      <h3 class="explorer-title">{{ t('step5.explorer.title') }}</h3>
      <span class="results-count">{{ t('step5.explorer.resultsCount', { count: totalCount }) }}</span>
    </div>

    <!-- Search -->
    <div class="explorer-search-bar">
      <input
        v-model="searchInput"
        type="search"
        class="explorer-search"
        :placeholder="t('step5.explorer.searchPlaceholder')"
      />
      <div v-if="searchQuery" class="search-badge">
        <span>{{ searchQuery }}</span>
        <button class="search-clear" @click="clearSearch">×</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="explorer-filters">
      <select v-model="filters.agent" class="filter-select" @change="currentPage = 1">
        <option value="">{{ t('step5.explorer.filterAgent') }} — {{ t('step5.explorer.all') }}</option>
        <option v-for="name in uniqueAgents" :key="name" :value="name">{{ name }}</option>
      </select>

      <select v-model="filters.platform" class="filter-select" @change="currentPage = 1">
        <option value="">{{ t('step5.explorer.filterPlatform') }} — {{ t('step5.explorer.all') }}</option>
        <option value="twitter">Twitter</option>
        <option value="reddit">Reddit</option>
      </select>

      <select v-model="filters.actionType" class="filter-select" @change="currentPage = 1">
        <option value="">{{ t('step5.explorer.filterActionType') }} — {{ t('step5.explorer.all') }}</option>
        <option v-for="type in uniqueActionTypes" :key="type" :value="type">{{ t(`step5.actions.types.${type}`) || type }}</option>
      </select>

      <select v-model="filters.round" class="filter-select" @change="currentPage = 1">
        <option value="">{{ t('step5.explorer.filterRound') }} — {{ t('step5.explorer.all') }}</option>
        <option v-for="r in uniqueRounds" :key="r" :value="String(r)">{{ r }}</option>
      </select>

      <select v-model="filters.success" class="filter-select" @change="currentPage = 1">
        <option value="">{{ t('step5.explorer.filterSuccess') }} — {{ t('step5.explorer.all') }}</option>
        <option value="true">{{ t('step5.explorer.success') }}</option>
        <option value="false">{{ t('step5.explorer.failure') }}</option>
      </select>

      <button class="filter-clear-btn" @click="clearFilters">
        {{ t('step5.explorer.clearFilters') }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="explorer-loading">
      <div class="loading-spinner"></div>
      <span>{{ t('common.loading') }}</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="explorer-error">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-else class="explorer-table-wrapper">
      <table class="explorer-table">
        <thead>
          <tr>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'round_num' }"
              @click="setSort('round_num')"
            >
              {{ t('step5.explorer.colRound') }}
              <span v-if="sortKey === 'round_num'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'timestamp' }"
              @click="setSort('timestamp')"
            >
              {{ t('step5.explorer.colTime') }}
              <span v-if="sortKey === 'timestamp'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'agent_name' }"
              @click="setSort('agent_name')"
            >
              {{ t('step5.explorer.colAgent') }}
              <span v-if="sortKey === 'agent_name'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'platform' }"
              @click="setSort('platform')"
            >
              {{ t('step5.explorer.colPlatform') }}
              <span v-if="sortKey === 'platform'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'action_type' }"
              @click="setSort('action_type')"
            >
              {{ t('step5.explorer.colAction') }}
              <span v-if="sortKey === 'action_type'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th>{{ t('step5.explorer.colContent') }}</th>
            <th
              class="sortable-header"
              :class="{ active: sortKey === 'success' }"
              @click="setSort('success')"
            >
              {{ t('step5.explorer.colSuccess') }}
              <span v-if="sortKey === 'success'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="action in paginatedActions" :key="action.id || action.timestamp" class="explorer-row">
            <td>{{ action.round_num }}</td>
            <td>{{ formatTime(action.timestamp) }}</td>
            <td>{{ action.agent_name }}</td>
            <td>
              <span class="platform-badge" :class="action.platform">{{ action.platform }}</span>
            </td>
            <td>{{ t(`step5.actions.types.${action.action_type}`) || action.action_type }}</td>
            <td class="content-cell">{{ getContentPreview(action) }}</td>
            <td>
              <span v-if="action.success" class="success-badge">{{ t('step5.explorer.success') }}</span>
              <span v-else class="error-badge">{{ t('step5.explorer.failure') }}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty state -->
      <div v-if="paginatedActions.length === 0" class="explorer-empty">
        <p>{{ t('step5.explorer.noData') }}</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="!loading && !error && filteredActions.length > 0" class="explorer-pagination">
      <button
        class="page-btn prev"
        :disabled="currentPage === 1"
        @click="currentPage--"
      >
        {{ t('step5.explorer.prevPage') }}
      </button>

      <div class="page-numbers">
        <button
          v-for="p in visiblePages"
          :key="p"
          class="page-number"
          :class="{ active: p === currentPage }"
          @click="currentPage = p"
        >
          {{ p }}
        </button>
      </div>

      <button
        class="page-btn next"
        :disabled="currentPage === totalPages"
        @click="currentPage++"
      >
        {{ t('step5.explorer.nextPage') }}
      </button>

      <span class="pagination-info">
        {{ t('step5.explorer.pageInfo', { page: currentPage, total: totalPages, count: filteredActions.length }) }}
      </span>

      <select v-model="pageSize" class="page-size-select" @change="currentPage = 1">
        <option v-for="size in [10, 25, 50, 100]" :key="size" :value="size">{{ size }} / página</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSimulationActions, getSimulationPosts } from '../api/simulation'

const { t } = useI18n()

const props = defineProps({
  simulationId: { type: String, required: true }
})

// State
const actions = ref([])
const posts = ref([])
const loading = ref(false)
const error = ref(null)
const filters = ref({ agent: '', platform: '', actionType: '', round: '', success: '' })
const searchQuery = ref('')
const searchInput = ref('')
const sortKey = ref('timestamp')
const sortOrder = ref('desc')
const pageSize = ref(25)
const currentPage = ref(1)
const totalCount = ref(0)

// Debounce timer
let searchDebounceTimer = null

// Watch search input with debounce
watch(searchInput, (val) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    searchQuery.value = val.trim()
    currentPage.value = 1
  }, 300)
})

// Unique filter options
const uniqueAgents = computed(() => {
  const names = new Set(actions.value.map(a => a.agent_name).filter(Boolean))
  return Array.from(names).sort()
})

const knownActionTypes = ['CREATE_POST', 'LIKE_POST', 'QUOTE_POST', 'REPOST_POST', 'CREATE_COMMENT', 'FOLLOW']

const uniqueActionTypes = computed(() => {
  const types = new Set(actions.value.map(a => a.action_type).filter(Boolean))
  knownActionTypes.forEach(t => types.add(t))
  return Array.from(types).sort()
})

const uniqueRounds = computed(() => {
  const rounds = new Set(actions.value.map(a => a.round_num).filter(n => n !== undefined && n !== null))
  return Array.from(rounds).sort((a, b) => a - b)
})

// Filtered actions
const filteredActions = computed(() => {
  let result = actions.value

  // Text search
  const query = searchQuery.value.toLowerCase()
  if (query.length >= 1) {
    let relatedAgentIds = new Set()
    let relatedRounds = new Set()

    if (query.length >= 2) {
      posts.value.forEach(post => {
        const content = (post.content || '').toLowerCase()
        if (content.includes(query)) {
          relatedAgentIds.add(post.agent_id)
          relatedRounds.add(post.round_num)
        }
      })
    }

    result = result.filter(action => {
      const resultText = (action.result || '').toLowerCase()
      const argsContent = (action.action_args?.content || '').toLowerCase()
      const matchesContent = resultText.includes(query) || argsContent.includes(query)
      const matchesRelated = relatedAgentIds.has(action.agent_id) || relatedRounds.has(action.round_num)
      return matchesContent || matchesRelated
    })
  }

  // Dropdown filters
  if (filters.value.agent) {
    result = result.filter(a => a.agent_name === filters.value.agent)
  }
  if (filters.value.platform) {
    result = result.filter(a => a.platform === filters.value.platform)
  }
  if (filters.value.actionType) {
    result = result.filter(a => a.action_type === filters.value.actionType)
  }
  if (filters.value.round) {
    result = result.filter(a => String(a.round_num) === filters.value.round)
  }
  if (filters.value.success) {
    const boolVal = filters.value.success === 'true'
    result = result.filter(a => a.success === boolVal)
  }

  // Sorting
  result = [...result].sort((a, b) => {
    let va = a[sortKey.value]
    let vb = b[sortKey.value]

    if (typeof va === 'string') va = va.toLowerCase()
    if (typeof vb === 'string') vb = vb.toLowerCase()

    if (va === undefined || va === null) va = ''
    if (vb === undefined || vb === null) vb = ''

    if (va < vb) return sortOrder.value === 'asc' ? -1 : 1
    if (va > vb) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return result
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredActions.value.length / pageSize.value))
})

const paginatedActions = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredActions.value.slice(start, start + pageSize.value)
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const maxVisible = 5

  if (total <= maxVisible) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + maxVisible - 1)

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
})

// Methods
const loadActions = async () => {
  if (!props.simulationId) return
  loading.value = true
  error.value = null
  try {
    const res = await getSimulationActions(props.simulationId, { limit: 1000, offset: 0 })
    if (res.success && res.data) {
      actions.value = res.data.actions || []
      totalCount.value = res.data.count || actions.value.length
    } else {
      throw new Error(res.error || 'Failed to load actions')
    }
  } catch (err) {
    error.value = err.message || t('common.unknownError')
  } finally {
    loading.value = false
  }
}

const loadPosts = async () => {
  if (!props.simulationId) return
  try {
    const [redditRes, twitterRes] = await Promise.all([
      getSimulationPosts(props.simulationId, 'reddit', 500, 0),
      getSimulationPosts(props.simulationId, 'twitter', 500, 0)
    ])
    const redditPosts = redditRes.success && redditRes.data ? (redditRes.data.posts || []) : []
    const twitterPosts = twitterRes.success && twitterRes.data ? (twitterRes.data.posts || []) : []
    posts.value = [...redditPosts, ...twitterPosts]
  } catch (err) {
    // Non-critical: posts are only for cross-referencing search
    posts.value = []
  }
}

const setSort = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const clearFilters = () => {
  filters.value = { agent: '', platform: '', actionType: '', round: '', success: '' }
  currentPage.value = 1
}

const clearSearch = () => {
  searchInput.value = ''
  searchQuery.value = ''
  currentPage.value = 1
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('pt-BR', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

const getContentPreview = (action) => {
  const text = action.result || action.action_args?.content || ''
  return text.length > 80 ? text.slice(0, 80) + '…' : text
}

// Lifecycle
onMounted(() => {
  if (props.simulationId) {
    loadActions()
    loadPosts()
  }
})

watch(() => props.simulationId, (newId) => {
  if (newId) {
    loadActions()
    loadPosts()
  }
})
</script>

<style scoped>
.action-explorer {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
}

.explorer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline);
}

.explorer-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-on-background);
  margin: 0;
}

.results-count {
  font-size: 12px;
  color: var(--color-muted);
}

.explorer-search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-outline);
}

.explorer-search {
  flex: 1;
  padding: 8px 12px;
  font-size: 13px;
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-on-surface);
  transition: border-color 0.2s ease;
}

.explorer-search:focus {
  outline: none;
  border-color: var(--color-on-background);
}

.search-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 20px;
  font-size: 12px;
  color: var(--color-on-surface);
}

.search-clear {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  color: var(--color-on-surface);
  line-height: 1;
}

.search-clear:hover {
  background: var(--color-muted);
}

.explorer-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--color-outline);
  flex-wrap: wrap;
}

.filter-select {
  padding: 6px 10px;
  font-size: 12px;
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-on-surface);
  cursor: pointer;
  min-width: 140px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-on-background);
}

.filter-clear-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-clear-btn:hover {
  color: var(--color-on-surface);
  border-color: var(--color-on-background);
}

.explorer-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-muted);
}

.explorer-error {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-error);
  font-size: 14px;
  padding: 40px;
}

.explorer-table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.explorer-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 700px;
}

.explorer-table thead th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 1;
}

.explorer-table thead th.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s ease;
}

.explorer-table thead th.sortable-header:hover {
  color: var(--color-on-background);
}

.explorer-table thead th.sortable-header.active {
  color: var(--color-on-background);
}

.sort-arrow {
  margin-left: 4px;
  font-size: 10px;
}

.explorer-row td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-outline);
  color: var(--color-on-surface);
  vertical-align: top;
}

.explorer-row:hover td {
  background: var(--color-surface-container-low);
}

.content-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--color-muted);
}

.platform-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-radius: 4px;
}

.platform-badge.twitter {
  background: rgba(29, 161, 242, 0.1);
  color: #1DA1F2;
}

.platform-badge.reddit {
  background: rgba(255, 69, 0, 0.1);
  color: #FF4500;
}

.success-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  background: #D1FAE5;
  color: #047857;
  border-radius: 4px;
}

.error-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  background: #FEE2E2;
  color: #DC2626;
  border-radius: 4px;
}

.explorer-empty {
  padding: 60px 20px;
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
}

.explorer-pagination {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--color-outline);
  background: var(--color-surface);
  flex-wrap: wrap;
}

.page-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-surface);
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-on-background);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-number:hover {
  color: var(--color-on-surface);
  background: var(--color-surface-container-low);
}

.page-number.active {
  color: var(--color-surface);
  background: var(--color-on-background);
  border-color: var(--color-on-background);
}

.pagination-info {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-muted);
}

.page-size-select {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-on-surface);
  cursor: pointer;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-outline);
  border-top-color: var(--color-on-background);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

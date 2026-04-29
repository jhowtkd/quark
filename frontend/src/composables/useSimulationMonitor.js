import { ref, watch, onMounted, onUnmounted } from 'vue'
import { getRunStatus, getRunStatusDetail } from '../api/simulation.js'

const POLL_INTERVAL_RUNNING = 3000
const POLL_INTERVAL_IDLE = 10000
const MAX_BACKOFF_MS = 30000

export function useSimulationMonitor(simulationIdRef) {
  const state = ref(null)
  const actions = ref([])
  const isPolling = ref(false)
  const error = ref(null)
  const errorCount = ref(0)

  let statusTimer = null
  let actionIds = new Set()

  const getInterval = () => {
    if (state.value?.runner_status === 'running') {
      const backoff = Math.min(3000 * (2 ** errorCount.value), MAX_BACKOFF_MS)
      return Math.max(POLL_INTERVAL_RUNNING, backoff)
    }
    return POLL_INTERVAL_IDLE
  }

  const fetchStatus = async () => {
    if (!simulationIdRef.value) return false
    const id = simulationIdRef.value
    try {
      const res = await getRunStatus(id)
      if (simulationIdRef.value !== id) return false
      if (res.success && res.data) {
        state.value = res.data
        error.value = null
        errorCount.value = 0
      }
    } catch (err) {
      if (simulationIdRef.value !== id) return false
      error.value = err.message
      errorCount.value++
    }
    return true
  }

  const fetchDetail = async () => {
    if (!simulationIdRef.value) return false
    const id = simulationIdRef.value
    try {
      const res = await getRunStatusDetail(id)
      if (simulationIdRef.value !== id) return false
      if (res.success && res.data) {
        const serverActions = res.data.all_actions || []
        serverActions.forEach(action => {
          const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
          if (!actionIds.has(actionId)) {
            actionIds.add(actionId)
            actions.value.push({ ...action, _uniqueId: actionId })
          }
        })
      }
    } catch (err) {
      if (simulationIdRef.value !== id) return false
      // Silently fail detail fetch
    }
    return true
  }

  const tick = async () => {
    if (document.hidden) {
      scheduleNext()
      return
    }
    const ok = await fetchStatus()
    if (!ok) return
    const detailOk = await fetchDetail()
    if (!detailOk) return
    scheduleNext()
  }

  const scheduleNext = () => {
    if (!isPolling.value) return
    if (statusTimer) clearTimeout(statusTimer)
    statusTimer = setTimeout(tick, getInterval())
  }

  const startPolling = () => {
    if (isPolling.value) return
    isPolling.value = true
    errorCount.value = 0
    tick()
  }

  const stopPolling = () => {
    isPolling.value = false
    if (statusTimer) {
      clearTimeout(statusTimer)
      statusTimer = null
    }
  }

  const reset = () => {
    stopPolling()
    state.value = null
    actions.value = []
    actionIds = new Set()
    error.value = null
    errorCount.value = 0
  }

  const onVisibilityChange = () => {
    if (!document.hidden && isPolling.value) {
      tick()
    }
  }

  onMounted(() => {
    if (simulationIdRef.value && !isPolling.value) startPolling()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    reset()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  watch(simulationIdRef, (newId, oldId) => {
    if (newId !== oldId) {
      reset()
      if (newId) startPolling()
    }
  })

  return {
    state,
    actions,
    isPolling,
    error,
    errorCount,
    startPolling,
    stopPolling,
    reset,
  }
}

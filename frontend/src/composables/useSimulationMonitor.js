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
      const backoff = Math.min(2 ** errorCount.value * 1000, MAX_BACKOFF_MS)
      return Math.max(POLL_INTERVAL_RUNNING, backoff)
    }
    return POLL_INTERVAL_IDLE
  }

  const fetchStatus = async () => {
    if (!simulationIdRef.value) return
    try {
      const res = await getRunStatus(simulationIdRef.value)
      if (res.success && res.data) {
        state.value = res.data
        error.value = null
        errorCount.value = 0
      }
    } catch (err) {
      error.value = err.message
      errorCount.value++
    }
  }

  const fetchDetail = async () => {
    if (!simulationIdRef.value) return
    try {
      const res = await getRunStatusDetail(simulationIdRef.value)
      if (res.success && res.data) {
        const serverActions = res.data.all_actions || []
        serverActions.forEach(action => {
          const id = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
          if (!actionIds.has(id)) {
            actionIds.add(id)
            actions.value.push({ ...action, _uniqueId: id })
          }
        })
      }
    } catch (err) {
      // Silently fail detail fetch
    }
  }

  const tick = async () => {
    if (document.hidden) {
      scheduleNext()
      return
    }
    await fetchStatus()
    await fetchDetail()
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

  // Start polling immediately if simulationId is already provided
  // (onMounted won't fire in test contexts without a component host)
  if (simulationIdRef.value) startPolling()

  onMounted(() => {
    if (simulationIdRef.value && !isPolling.value) startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  watch(simulationIdRef, (newId, oldId) => {
    if (newId !== oldId) {
      reset()
      if (newId) startPolling()
    }
  })

  const onVisibilityChange = () => {
    if (!document.hidden && isPolling.value) {
      tick()
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    state,
    actions,
    isPolling,
    error,
    startPolling,
    stopPolling,
    reset,
  }
}

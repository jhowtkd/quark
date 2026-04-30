<template>
  <div class="simulation-panel">
    <!-- Top Control Bar -->
    <div class="control-bar">
      <div class="action-controls">
        <button
          class="action-btn secondary"
          :disabled="!state || state.runner_status !== 'running'"
          @click="handleStopSimulation"
        >
          {{ $t('step3.stopSimulationBtn') }}
        </button>
        <button 
          class="action-btn primary"
          :disabled="phase !== 2 || isGeneratingReport"
          @click="handleNextStep"
        >
          <span v-if="isGeneratingReport" class="loading-spinner-small"></span>
          {{ isGeneratingReport ? $t('step3.generatingReportBtn') : $t('step3.startGenerateReportBtn') }}
          <span v-if="!isGeneratingReport" class="arrow-icon">→</span>
        </button>
      </div>
    </div>

    <!-- Monitor Status Banners -->
    <div v-if="error" class="monitor-error-banner" role="alert">
      <span>Connection unstable. {{ error }}</span>
      <button v-if="!isPolling" class="retry-btn" @click="startPolling">Retry</button>
    </div>
    <div v-else-if="isPolling && !state" class="monitor-loading-banner" role="status">
      <span>Connecting to simulation...</span>
    </div>

    <!-- Monitor Tabs -->
    <div class="monitor-tabs-wrapper">
      <SimMonitorTabs :state="state" :actions="actions" />
    </div>

    <!-- Bottom Info / Logs -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SIMULATION MONITOR</span>
        <span class="log-id">{{ simulationId || 'NO_SIMULATION' }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, toRef } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  startSimulation,
  stopSimulation
} from '../api/simulation'
import { generateReport } from '../api/report'
import { useSimulationMonitor } from '../composables/useSimulationMonitor.js'
import SimMonitorTabs from './simulation/SimMonitorTabs.vue'

const { t } = useI18n()

const props = defineProps({
  simulationId: String,
  maxRounds: Number,
  minutesPerRound: {
    type: Number,
    default: 30
  },
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()

// State
const isGeneratingReport = ref(false)
const phase = ref(0)
const logContent = ref(null)

// Composable
const simulationIdRef = toRef(props, 'simulationId')
const { state, actions, isPolling, error, startPolling, stopPolling, reset } = useSimulationMonitor(simulationIdRef)

// Watch for completion
watch(state, (newState) => {
  if (newState?.runner_status === 'completed' || newState?.runner_status === 'stopped') {
    phase.value = 2
    stopPolling()
    emit('update-status', 'completed')
  }
}, { immediate: false })

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

// Reset all state
const resetAllState = () => {
  phase.value = 0
  reset()
}

// Iniciar simulação
const doStartSimulation = async () => {
  if (!props.simulationId) {
    addLog(t('log.errorMissingSimId'))
    return
  }

  resetAllState()
  
  addLog(t('log.startingDualSim'))
  emit('update-status', 'processing')
  
  try {
    const params = {
      simulation_id: props.simulationId,
      platform: 'parallel',
      force: true,
      enable_graph_memory_update: true
    }
    
    if (props.maxRounds) {
      params.max_rounds = props.maxRounds
      addLog(t('log.setMaxRounds', { rounds: props.maxRounds }))
    }
    
    addLog(t('log.graphMemoryUpdateEnabled'))
    
    const res = await startSimulation(params)
    
    if (res.success && res.data) {
      if (res.data.force_restarted) {
        addLog(t('log.oldSimCleared'))
      }
      addLog(t('log.engineStarted'))
      addLog(`  ├─ PID: ${res.data.process_pid || '-'}`)
      
      phase.value = 1
      reset()
      startPolling()
    } else {
      addLog(t('log.startFailed', { error: res.error || t('common.unknownError') }))
      emit('update-status', 'error')
    }
  } catch (err) {
    addLog(t('log.startException', { error: err.message }))
    emit('update-status', 'error')
  }
}

const handleStopSimulation = async () => {
  if (!props.simulationId) return
  addLog(t('log.stoppingSim'))
  try {
    const res = await stopSimulation({ simulation_id: props.simulationId })
    if (res.success) {
      addLog(t('log.simStoppedSuccess'))
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    } else {
      addLog(t('log.stopFailed', { error: res.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('log.stopException', { error: err.message }))
  }
}

const handleNextStep = async () => {
  if (!props.simulationId) {
    addLog(t('log.errorMissingSimId'))
    return
  }

  if (isGeneratingReport.value) {
    addLog(t('log.reportRequestSent'))
    return
  }
  
  isGeneratingReport.value = true
  addLog(t('log.startingReportGen'))
  
  try {
    const res = await generateReport({
      simulation_id: props.simulationId,
      force_regenerate: true
    })
    
    if (res.success && res.data) {
      const reportId = res.data.report_id
      addLog(t('log.reportGenTaskStarted', { reportId }))
      
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog(t('log.reportGenFailed', { error: res.error || t('common.unknownError') }))
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(t('log.reportGenException', { error: err.message }))
    isGeneratingReport.value = false
  }
}

// Scroll log to bottom
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  addLog(t('log.step3Init'))
  if (props.simulationId) {
    doStartSimulation()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  overflow: hidden;
}

/* --- Control Bar --- */
.control-bar {
  background: var(--color-surface);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-outline);
  z-index: 10;
  height: 64px;
}

/* Action Button */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 0px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: var(--font-machine);
}

.action-btn.primary {
  background: var(--color-on-background);
  color: var(--color-surface-container-highest);
  border: none;
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.action-btn.secondary {
  background: var(--color-surface-container-highest);
  color: var(--color-on-background);
  border: 1px solid var(--color-on-background);
}

.action-btn.secondary:hover:not(:disabled) {
  background: var(--color-on-background);
  color: var(--color-surface-container-highest);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* Monitor Tabs */
.monitor-tabs-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Logs */
.system-logs {
  background: var(--color-on-background);
  color: var(--color-outline);
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid var(--color-surface-elevated);
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-on-surface);
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: var(--color-muted);
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar { width: 4px; }
.log-content::-webkit-scrollbar-thumb { background: var(--color-on-surface); border-radius: 2px; }

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time { color: var(--color-muted); min-width: 75px; }
.log-msg { color: var(--color-disabled); word-break: break-all; }
.mono { font-family: 'JetBrains Mono', monospace; }

.monitor-error-banner {
  padding: 10px 16px;
  background: var(--color-error-container);
  color: var(--color-on-error-container);
  font-size: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-outline);
}
.retry-btn {
  padding: 4px 10px;
  background: var(--color-error);
  color: var(--color-on-error);
  border: none;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}
.monitor-loading-banner {
  padding: 10px 16px;
  background: var(--color-surface-container-high);
  color: var(--color-muted);
  font-size: 12px;
  border-bottom: 1px solid var(--color-outline);
}

/* Loading spinner for button */
.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid color-mix(in srgb, var(--color-on-surface) 30%, transparent);
  border-top-color: var(--color-on-surface);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}
</style>

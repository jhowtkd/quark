<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">FUTUR.IA</div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: $t('main.layoutGraph'), split: $t('main.layoutSplit'), workbench: $t('main.layoutWorkbench') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSwitcher />
        <div class="step-divider"></div>
        <div class="workflow-step">
          <span class="step-num">Step {{ currentStep }}/5</span>
          <span class="step-name">{{ $tm('main.stepNames')[currentStep - 1] }}</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="currentPhase"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step Components -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <!-- Step 1: 图谱Construir DB -->
        <Step1GraphBuild 
          v-if="currentStep === 1"
          :currentPhase="currentPhase"
          :projectData="projectData"
          :ontologyProgress="ontologyProgress"
          :buildProgress="buildProgress"
          :graphData="graphData"
          :chunkSize="chunkSize"
          :chunkOverlap="chunkOverlap"
          :costPreview="costPreview"
          :previewLoading="previewLoading"
          :graphActionError="graphActionError"
          :systemLogs="systemLogs"
          :researchMode="researchMode"
          :researchStatus="researchStatus"
          :researchResult="researchResult"
          :researchRunId="researchRunId"
          :researchActionError="researchActionError"
          :ontologyGenerating="ontologyGenerating"
          @update-chunk-settings="handleChunkSettingsUpdate"
          @request-preview="requestBuildPreview"
          @confirm-build="startBuildGraph"
          @next-step="handleNextStep"
          @enter-research-mode="enterResearchMode"
          @start-research="startResearchRun"
          @approve-research="approveResearchRun"
          @reject-research="rejectResearchRun"
          @rerun-research="rerunResearchRun"
          @promote-success="handlePromoteSuccess"
        />
        <!-- Step 2: 环境搭建 -->
        <Step2EnvSetup
          v-else-if="currentStep === 2"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GraphPanel from '../components/GraphPanel.vue'
import Step1GraphBuild from '../components/Step1GraphBuild.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { generateOntology, generateOntologyFromText, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { startResearch, getResearchStatus, approveResearch, rejectResearch, rerunResearch } from '../api/research'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const route = useRoute()
const router = useRouter()
const { t, tm } = useI18n()

// Layout State
const viewMode = ref('split') // graph | split | workbench

// Step State
const currentStep = ref(1) // 1: 图谱Construir DB, 2: 环境搭建, 3: Start Motor, 4: Sínteses sendo emitidas..., 5: Deep Dive Interact.
const stepNames = computed(() => tm('main.stepNames'))

// Data State
const currentProjectId = ref(route.params.projectId)
const loading = ref(false)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const currentPhase = ref(-1) // -1: Upload, 0: Ontology, 1: Build, 2: Complete
const ontologyProgress = ref(null)
const buildProgress = ref(null)
const chunkSize = ref(300)
const chunkOverlap = ref(30)
const costPreview = ref(null)
const previewLoading = ref(false)
const graphActionError = ref('')
const systemLogs = ref([])

// Research State
const researchMode = ref('basic') // 'basic' | 'deep'
const researchRunId = ref(null)
const researchStatus = ref(null) // { status, progress, message, error }
const researchResult = ref(null) // { markdown, connector_used }
const researchActionError = ref('')
const ontologyGenerating = ref(false)
let researchPollTimer = null

// Polling timers
let pollTimer = null
let graphPollTimer = null

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return 'Error'
  if (currentPhase.value >= 2) return 'Ready'
  if (currentPhase.value === 1) return 'Building Graph'
  if (previewLoading.value) return 'Estimating Cost'
  if (costPreview.value) return 'Ready to Build'
  if (projectData.value?.status === 'ontology_generated') return 'Review Build Settings'
  if (currentPhase.value === 0) return 'Generating Ontology'
  return 'Initializing'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  // Keep last 100 logs
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const applyChunkSettings = (source = {}) => {
  const nextChunkSize = Number(source.chunk_size ?? source.chunkSize ?? chunkSize.value)
  const nextChunkOverlap = Number(source.chunk_overlap ?? source.chunkOverlap ?? chunkOverlap.value)

  if (Number.isFinite(nextChunkSize)) {
    chunkSize.value = nextChunkSize
  }
  if (Number.isFinite(nextChunkOverlap)) {
    chunkOverlap.value = nextChunkOverlap
  }

  if (projectData.value) {
    projectData.value = {
      ...projectData.value,
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value
    }
  }
}

const clearCostPreview = () => {
  if (currentPhase.value < 1) {
    costPreview.value = null
  }
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleNextStep = (params = {}) => {
  if (currentStep.value < 5) {
    currentStep.value++
    addLog(t('log.enterStep', { step: currentStep.value, name: stepNames.value[currentStep.value - 1] }))
    
    // 如果是从 Step 2 进入 Step 3，Fixar Max_rounds Sim.
    if (currentStep.value === 3 && params.maxRounds) {
      addLog(t('log.customSimRounds', { rounds: params.maxRounds }))
    }
  }
}

const handleGoBack = () => {
  if (currentStep.value > 1) {
    currentStep.value--
    addLog(t('log.returnToStep', { step: currentStep.value, name: stepNames.value[currentStep.value - 1] }))
  }
}

// --- Data Logic ---

const initProject = async () => {
  addLog('Project view initialized.')
  if (currentProjectId.value === 'new') {
    await handleNewProject()
  } else {
    await loadProject()
  }
}

const handleNewProject = async () => {
  const pending = getPendingUpload()
  if (!pending.isPending || pending.files.length === 0) {
    error.value = 'No pending files found.'
    addLog('Error: No pending files found for new project.')
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0
    ontologyProgress.value = { message: 'Uploading and analyzing docs...' }
    addLog('Starting ontology generation: Uploading files...')
    
    const formData = new FormData()
    pending.files.forEach(f => formData.append('files', f))
    formData.append('simulation_requirement', pending.simulationRequirement)
    
    const res = await generateOntology(formData)
    if (res.success) {
      clearPendingUpload()
      currentProjectId.value = res.data.project_id
      projectData.value = {
        ...res.data,
        status: 'ontology_generated'
      }
      applyChunkSettings(res.data)
      
      router.replace({ name: 'Process', params: { projectId: res.data.project_id } })
      ontologyProgress.value = null
      addLog(`Ontology generated successfully for project ${res.data.project_id}`)
      addLog('Build settings ready for review. Generate a cost preview before starting the graph build.')
    } else {
      error.value = res.error || 'Ontology generation failed'
      addLog(`Error generating ontology: ${error.value}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in handleNewProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const loadProject = async () => {
  try {
    loading.value = true
    addLog(`Loading project ${currentProjectId.value}...`)
    const res = await getProject(currentProjectId.value)
    if (res.success) {
      projectData.value = res.data
      applyChunkSettings(res.data)
      updatePhaseByStatus(res.data.status)
      addLog(`Project loaded. Status: ${res.data.status}`)
      
      if (res.data.status === 'ontology_generated' && !res.data.graph_id) {
        addLog('Ontology is ready. Waiting for preview and explicit build confirmation.')
      } else if (res.data.status === 'graph_building' && res.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(res.data.graph_build_task_id)
        startGraphPolling()
      } else if (res.data.status === 'graph_completed' && res.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(res.data.graph_id)
      }
    } else {
      error.value = res.error
      addLog(`Error loading project: ${res.error}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in loadProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated': currentPhase.value = 0; break;
    case 'graph_building': currentPhase.value = 1; break;
    case 'graph_completed': currentPhase.value = 2; break;
    case 'failed': error.value = 'Project failed'; break;
  }
}

const handleChunkSettingsUpdate = (settings = {}) => {
  graphActionError.value = ''
  error.value = ''
  applyChunkSettings(settings)
  clearCostPreview()
  addLog(`Chunk settings updated to ${chunkSize.value}/${chunkOverlap.value}. Preview needs refresh.`)
}

const requestBuildPreview = async () => {
  try {
    previewLoading.value = true
    graphActionError.value = ''
    error.value = ''
    addLog(`Requesting ingestion cost preview with chunk settings ${chunkSize.value}/${chunkOverlap.value}...`)

    const res = await buildGraph({
      project_id: currentProjectId.value,
      preview: true,
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value
    })

    if (res.success) {
      costPreview.value = res.data
      applyChunkSettings(res.data)
      addLog(
        `Preview ready. ${res.data.chunk_count} chunks, ${res.data.estimated_total_bytes} bytes, ${res.data.estimated_credits} estimated credits.`
      )
    } else {
      graphActionError.value = res.error || 'Preview failed'
      addLog(`Preview failed: ${graphActionError.value}`)
    }
  } catch (err) {
    graphActionError.value = err.message
    addLog(`Exception while generating preview: ${err.message}`)
  } finally {
    previewLoading.value = false
  }
}

const startBuildGraph = async () => {
  if (!costPreview.value) {
    graphActionError.value = 'Preview required before starting the graph build.'
    addLog(graphActionError.value)
    return
  }

  if (costPreview.value?.ontology_guardrails?.can_build === false) {
    graphActionError.value = 'Ontology compatibility issues must be resolved before building the graph.'
    addLog(graphActionError.value)
    return
  }

  try {
    graphActionError.value = ''
    error.value = ''
    currentPhase.value = 1
    buildProgress.value = { progress: 0, message: 'Starting build...' }
    addLog(`Initiating graph build with chunk settings ${chunkSize.value}/${chunkOverlap.value}...`)
    
    const res = await buildGraph({
      project_id: currentProjectId.value,
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value
    })
    if (res.success) {
      addLog(`Graph build task started. Task ID: ${res.data.task_id}`)
      startGraphPolling()
      startPollingTask(res.data.task_id)
    } else {
      currentPhase.value = 0
      graphActionError.value = res.error || 'Build failed'
      addLog(`Error starting build: ${graphActionError.value}`)
      stopPolling()
    }
  } catch (err) {
    currentPhase.value = 0
    graphActionError.value = err.message
    addLog(`Exception in startBuildGraph: ${err.message}`)
    stopGraphPolling()
    stopPolling()
  }
}

const startGraphPolling = () => {
  addLog('Started polling for graph data...')
  fetchGraphData()
  graphPollTimer = setInterval(fetchGraphData, 10000)
}

const fetchGraphData = async () => {
  try {
    // Refresh project info to check for graph_id
    const projRes = await getProject(currentProjectId.value)
    if (projRes.success && projRes.data.graph_id) {
      const gRes = await getGraphData(projRes.data.graph_id)
      if (gRes.success) {
        graphData.value = gRes.data
        const nodeCount = gRes.data.node_count || gRes.data.nodes?.length || 0
        const edgeCount = gRes.data.edge_count || gRes.data.edges?.length || 0
        addLog(`Graph data refreshed. Nodes: ${nodeCount}, Edges: ${edgeCount}`)
      } else {
        // Non-success response from Zep (rate limit / usage limit) — stop polling
        addLog(`Graph API unavailable (${gRes.error || 'error'}). Stopping polling.`)
        stopPolling()
      }
    }
  } catch (err) {
    console.warn('Graph fetch error:', err)
    // On error, stop polling to avoid hammering Zep with requests
    stopPolling()
  }
}

const startPollingTask = (taskId) => {
  pollTaskStatus(taskId)
  pollTimer = setInterval(() => pollTaskStatus(taskId), 2000)
}

const pollTaskStatus = async (taskId) => {
  try {
    const res = await getTaskStatus(taskId)
    if (res.success) {
      const task = res.data
      
      // Log progress message if it changed
      if (task.message && task.message !== buildProgress.value?.message) {
        addLog(task.message)
      }
      
      buildProgress.value = { progress: task.progress || 0, message: task.message }
      
      if (task.status === 'completed') {
        addLog('Graph build task completed.')
        stopPolling()
        currentPhase.value = 2
        
        // Final load
        const projRes = await getProject(currentProjectId.value)
        if (projRes.success && projRes.data.graph_id) {
            projectData.value = projRes.data
            applyChunkSettings(projRes.data)
            await loadGraph(projRes.data.graph_id)
        }
      } else if (task.status === 'failed') {
        stopPolling()
        error.value = task.error
        addLog(`Graph build task failed: ${task.error}`)
      }
    }
  } catch (e) {
    console.error(e)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  addLog(`Loading full graph data: ${graphId}`)
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('Graph data loaded successfully.')
    } else {
      addLog(`Failed to load graph data: ${res.error}`)
    }
  } catch (e) {
    addLog(`Exception loading graph: ${e.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    addLog('Manual graph refresh triggered.')
    loadGraph(projectData.value.graph_id)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
    addLog('Graph polling stopped.')
  }
}

const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
    addLog('Graph polling stopped.')
  }
}

// --- Research Polling ---

const enterResearchMode = () => {
  researchMode.value = 'deep'
  researchActionError.value = ''
  addLog('Deep research mode enabled.')
}

const startResearchRun = async (query) => {
  try {
    researchMode.value = 'deep'
    researchActionError.value = ''
    addLog(`Starting deep research: ${query.substring(0, 50)}...`)
    
    const res = await startResearch({
      query,
      project_id: currentProjectId.value !== 'new' ? currentProjectId.value : undefined
    })
    
    if (res.success) {
      researchRunId.value = res.data.run_id
      researchStatus.value = { status: 'pending', progress: 0, message: 'Research queued' }
      addLog(`Research started. Run ID: ${res.data.run_id}`)
      startResearchPolling()
    } else {
      researchActionError.value = res.error || 'Failed to start research'
      addLog(`Failed to start research: ${researchActionError.value}`)
    }
  } catch (err) {
    researchActionError.value = err.message
    addLog(`Exception starting research: ${err.message}`)
  }
}

const startResearchPolling = () => {
  if (!researchRunId.value) return
  addLog('Started polling for research status...')
  pollResearchStatus()
  researchPollTimer = setInterval(pollResearchStatus, 5000)
}

const pollResearchStatus = async () => {
  if (!researchRunId.value) return
  
  try {
    const res = await getResearchStatus(researchRunId.value)
    if (res.success) {
      researchStatus.value = {
        status: res.data.status,
        progress: res.data.progress || 0,
        message: res.data.message || '',
        error: res.data.error || '',
        connector_used: res.data.connector_used || ''
      }
      
      // Log status changes
      const statusMsg = res.data.message || res.data.status
      if (statusMsg && statusMsg !== researchStatus.value?.lastMessage) {
        addLog(`Research: ${statusMsg}`)
        researchStatus.value.lastMessage = statusMsg
      }
      
      // Handle terminal states
      if (res.data.status === 'completed') {
        addLog('Research completed, loading result...')
        stopResearchPolling()
        await loadResearchResult()
      } else if (res.data.status === 'approved') {
        addLog('Research approved.')
        stopResearchPolling()
      } else if (res.data.status === 'failed') {
        addLog(`Research failed: ${res.data.error || 'Unknown error'}`)
        stopResearchPolling()
      }
    }
  } catch (e) {
    console.error('Research status poll error:', e)
  }
}

const loadResearchResult = async () => {
  if (!researchRunId.value) return
  
  try {
    const res = await getResearchResult(researchRunId.value)
    if (res.success) {
      researchResult.value = {
        markdown: res.data.markdown,
        connector_used: res.data.connector_used || ''
      }
      addLog('Research result loaded.')
    } else {
      addLog(`Failed to load research result: ${res.error}`)
    }
  } catch (e) {
    addLog(`Exception loading research result: ${e.message}`)
  }
}

const approveResearchRun = async () => {
  if (!researchRunId.value) return
  
  try {
    researchActionError.value = ''
    addLog('Approving research...')
    
    const res = await approveResearch(researchRunId.value)
    
    if (res.success) {
      researchStatus.value = { ...researchStatus.value, status: 'approved' }
      addLog('Research approved successfully.')
    } else {
      researchActionError.value = res.error || 'Failed to approve research'
      addLog(`Approve failed: ${researchActionError.value}`)
    }
  } catch (err) {
    researchActionError.value = err.message
    addLog(`Exception approving research: ${err.message}`)
  }
}

const rejectResearchRun = async () => {
  if (!researchRunId.value) return
  
  try {
    researchActionError.value = ''
    addLog('Rejecting research...')
    
    const res = await rejectResearch(researchRunId.value)
    
    if (res.success) {
      researchStatus.value = { ...researchStatus.value, status: 'pending' }
      addLog('Research rejected, reset to pending.')
    } else {
      researchActionError.value = res.error || 'Failed to reject research'
      addLog(`Reject failed: ${researchActionError.value}`)
    }
  } catch (err) {
    researchActionError.value = err.message
    addLog(`Exception rejecting research: ${err.message}`)
  }
}

const rerunResearchRun = async (feedback) => {
  if (!researchRunId.value) return
  
  try {
    researchActionError.value = ''
    addLog('Rerunning research with feedback...')
    
    const res = await rerunResearch(researchRunId.value, feedback)
    
    if (res.success) {
      // Update to new run ID
      const oldRunId = researchRunId.value
      researchRunId.value = res.data.new_run_id
      researchStatus.value = { status: 'pending', progress: 0, message: 'Rerun queued' }
      addLog(`Research rerun started. New Run ID: ${res.data.new_run_id}`)
      startResearchPolling()
    } else {
      researchActionError.value = res.error || 'Failed to rerun research'
      addLog(`Rerun failed: ${researchActionError.value}`)
    }
  } catch (err) {
    researchActionError.value = err.message
    addLog(`Exception rerunning research: ${err.message}`)
  }
}

const stopResearchPolling = () => {
  if (researchPollTimer) {
    clearInterval(researchPollTimer)
    researchPollTimer = null
    addLog('Research polling stopped.')
  }
}

const handlePromoteSuccess = async (result) => {
  // Stop research polling before initiating graph build
  stopResearchPolling()
  
  addLog('Research promotion successful, preparing graph build...')
  
  // Handle new project_id if returned (createProjectFromResearch case)
  if (result?.project_id && result.project_id !== currentProjectId.value) {
    addLog(`New project created: ${result.project_id}`)
    currentProjectId.value = result.project_id
    
    // Update URL to reflect new project
    if (route.params.projectId !== result.project_id) {
      router.replace({ name: 'Process', params: { projectId: result.project_id } })
    }
    
    // Reload project with new ID
    await loadProject()
  } else if (result?.project_id) {
    // Same project promoted - reload to pick up promoted content
    addLog(`Research promoted to existing project ${result.project_id}, reloading...`)
    await loadProject()
  }
  
  // Check if ontology is stub (both entity_types and edge_types are empty)
  const ontology = projectData.value?.ontology
  const hasStubOntology = !ontology?.entity_types?.length && !ontology?.edge_types?.length
  
  if (hasStubOntology && projectData.value?.project_id) {
    // Stub ontology detected - need to generate ontology from text
    addLog('Stub ontology detected, generating ontology from research text...')
    ontologyGenerating.value = true
    
    try {
      const simReq = projectData.value?.simulation_requirement || 'Generate comprehensive entity types and relationships for this knowledge graph'
      const genRes = await generateOntologyFromText(
        projectData.value.project_id,
        simReq
      )
      
      if (genRes.success) {
        addLog(`Ontology generated: ${genRes.data.entity_count} entities, ${genRes.data.edge_count} relations`)
        // Reload project to get updated ontology
        await loadProject()
      } else {
        addLog(`Ontology generation failed: ${genRes.error}`)
        graphActionError.value = genRes.error || 'Ontology generation failed'
      }
    } catch (err) {
      addLog(`Ontology generation exception: ${err.message}`)
      graphActionError.value = err.message
    } finally {
      ontologyGenerating.value = false
    }
  }
  
  // After promotion and optional ontology generation, trigger graph build path
  // Request preview first, then auto-start build
  await requestBuildPreview()
  
  // Only start build if preview succeeded
  if (costPreview.value) {
    await startBuildGraph()
  } else {
    addLog('Warning: preview failed after promotion, manual build required.')
  }
}

onMounted(() => {
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
  stopResearchPolling()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>

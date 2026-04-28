<template>
  <div class="workbench-panel">
    <div class="scroll-container">
      <div class="step-card" :class="{ active: currentPhase === 0 && !ontologyReady, completed: ontologyReady || currentPhase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">{{ $t('step1.ontologyGeneration') }}</span>
          </div>
          <div class="step-status">
            <span v-if="ontologyReady || currentPhase > 0" class="badge success">{{ $t('step1.ontologyCompleted') }}</span>
            <span v-else-if="currentPhase === 0" class="badge processing">{{ $t('step1.ontologyGenerating') }}</span>
            <span v-else class="badge pending">{{ $t('step1.ontologyPending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/graph/ontology/generate</p>
          <p class="description">{{ $t('step1.ontologyDesc') }}</p>

          <div v-if="currentPhase === 0 && ontologyProgress" class="progress-section">
            <div class="spinner-sm"></div>
            <span>{{ ontologyProgress.message || $t('step1.analyzingDocs') }}</span>
          </div>

          <div v-if="selectedOntologyItem" class="ontology-detail-overlay">
            <div class="detail-header">
              <div class="detail-title-group">
                <span class="detail-type-badge">{{ selectedOntologyItem.itemType === 'entity' ? 'ENTITY' : 'RELATION' }}</span>
                <span class="detail-name">{{ selectedOntologyItem.name }}</span>
              </div>
              <button class="close-btn" @click="selectedOntologyItem = null"><Icon name="x" :size="16" /></button>
            </div>
            <div class="detail-body">
              <div class="detail-desc">{{ selectedOntologyItem.description }}</div>

              <div v-if="selectedOntologyItem.attributes?.length" class="detail-section">
                <span class="section-label">ATTRIBUTES</span>
                <div class="attr-list">
                  <div v-for="attr in selectedOntologyItem.attributes" :key="attr.name" class="attr-item">
                    <span class="attr-name">{{ attr.name }}</span>
                    <span class="attr-type">({{ attr.type }})</span>
                    <span class="attr-desc">{{ attr.description }}</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedOntologyItem.examples?.length" class="detail-section">
                <span class="section-label">EXAMPLES</span>
                <div class="example-list">
                  <span v-for="example in selectedOntologyItem.examples" :key="example" class="example-tag">{{ example }}</span>
                </div>
              </div>

              <div v-if="selectedOntologyItem.source_targets?.length" class="detail-section">
                <span class="section-label">CONNECTIONS</span>
                <div class="conn-list">
                  <div v-for="(connection, index) in selectedOntologyItem.source_targets" :key="index" class="conn-item">
                    <span class="conn-node">{{ connection.source }}</span>
                    <span class="conn-arrow">→</span>
                    <span class="conn-node">{{ connection.target }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="projectData?.ontology?.entity_types" class="tags-container" :class="{ dimmed: selectedOntologyItem }">
            <span class="tag-label">GENERATED ENTITY TYPES</span>
            <div class="tags-list">
              <span
                v-for="entity in projectData.ontology.entity_types"
                :key="entity.name"
                class="entity-tag clickable"
                @click="selectOntologyItem(entity, 'entity')"
              >
                {{ entity.name }}
              </span>
            </div>
          </div>

          <div v-if="projectData?.ontology?.edge_types" class="tags-container" :class="{ dimmed: selectedOntologyItem }">
            <span class="tag-label">GENERATED RELATION TYPES</span>
            <div class="tags-list">
              <span
                v-for="relation in projectData.ontology.edge_types"
                :key="relation.name"
                class="entity-tag clickable"
                @click="selectOntologyItem(relation, 'relation')"
              >
                {{ relation.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: currentPhase === 1 || previewReady || ontologyReady, completed: currentPhase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">{{ $t('step1.graphRagBuild') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 1" class="badge success">{{ $t('step1.ontologyCompleted') }}</span>
            <span v-else-if="currentPhase === 1" class="badge processing">{{ buildProgress?.progress || 0 }}%</span>
            <span v-else-if="previewReady" class="badge success">{{ $t('step1.previewReady') }}</span>
            <span v-else class="badge pending">{{ $t('step1.ontologyPending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/graph/build</p>
          <p class="description">{{ $t('step1.graphRagDesc') }}</p>

          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.nodes }}</span>
              <span class="stat-label">{{ $t('step1.entityNodes') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.edges }}</span>
              <span class="stat-label">{{ $t('step1.relationEdges') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.types }}</span>
              <span class="stat-label">{{ $t('step1.schemaTypes') }}</span>
            </div>
          </div>

          <div class="control-grid">
            <label class="field-group">
              <span class="field-label">{{ $t('step1.chunkSize') }}</span>
              <input
                class="field-input"
                type="number"
                min="1"
                :disabled="controlsLocked"
                :value="chunkSize"
                @input="updateChunk('chunkSize', $event)"
              />
              <span class="field-hint">{{ $t('step1.chunkSizeHint') }}</span>
            </label>

            <label class="field-group">
              <span class="field-label">{{ $t('step1.chunkOverlap') }}</span>
              <input
                class="field-input"
                type="number"
                min="0"
                :disabled="controlsLocked"
                :value="chunkOverlap"
                @input="updateChunk('chunkOverlap', $event)"
              />
              <span class="field-hint">{{ $t('step1.chunkOverlapHint') }}</span>
            </label>
          </div>

          <div v-if="graphActionError" class="callout error">
            {{ graphActionError }}
          </div>

          <div v-if="currentPhase === 0 && ontologyReady" class="action-stack">
            <div v-if="!previewReady" class="callout neutral">
              {{ $t('step1.previewRequired') }}
            </div>

            <div v-if="previewReady" class="preview-card" :class="{ warning: costPreview?.warning_level === 'warning' }">
              <div class="preview-header">
                <span class="preview-title">{{ $t('step1.previewSummary') }}</span>
                <span class="preview-pill" :class="costPreview?.warning_level === 'warning' ? 'warning' : 'safe'">
                  {{ costPreview?.warning_level === 'warning' ? $t('step1.warningEstimate') : $t('step1.safeEstimate') }}
                </span>
              </div>

              <div class="preview-grid">
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.chunk_count || 0 }}</span>
                  <span class="preview-label">{{ $t('step1.previewChunks') }}</span>
                </div>
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.estimated_total_chars || 0 }}</span>
                  <span class="preview-label">{{ $t('step1.previewChars') }}</span>
                </div>
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.estimated_total_bytes || 0 }}</span>
                  <span class="preview-label">{{ $t('step1.previewBytes') }}</span>
                </div>
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.estimated_credits || 0 }}</span>
                  <span class="preview-label">{{ $t('step1.previewCredits') }}</span>
                </div>
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.chunk_size || chunkSize }}</span>
                  <span class="preview-label">{{ $t('step1.normalizedChunkSize') }}</span>
                </div>
                <div class="preview-stat">
                  <span class="preview-value">{{ costPreview?.chunk_overlap || chunkOverlap }}</span>
                  <span class="preview-label">{{ $t('step1.normalizedChunkOverlap') }}</span>
                </div>
              </div>
            </div>

            <div
              v-if="ontologyGuardrails && (ontologyGuardrails.warnings?.length || ontologyGuardrails.errors?.length)"
              class="guardrail-card"
              :class="{ blocking: ontologyGuardrails.can_build === false }"
            >
              <div class="guardrail-header">
                <span class="guardrail-title">{{ $t('step1.schemaGuardrailTitle') }}</span>
                <span class="guardrail-pill" :class="ontologyGuardrails.can_build === false ? 'blocking' : 'warning'">
                  {{ ontologyGuardrails.can_build === false ? $t('step1.schemaGuardrailBlocking') : $t('step1.schemaGuardrailWarning') }}
                </span>
              </div>

              <div v-if="ontologyGuardrails.errors?.length" class="guardrail-group">
                <span class="guardrail-label">{{ $t('step1.schemaGuardrailErrors') }}</span>
                <ul class="guardrail-list">
                  <li v-for="error in ontologyGuardrails.errors" :key="error">{{ error }}</li>
                </ul>
              </div>

              <div v-if="ontologyGuardrails.warnings?.length" class="guardrail-group">
                <span class="guardrail-label">{{ $t('step1.schemaGuardrailWarnings') }}</span>
                <ul class="guardrail-list">
                  <li v-for="warning in ontologyGuardrails.warnings" :key="warning">{{ warning }}</li>
                </ul>
              </div>
            </div>

            <div class="button-row">
              <button
                class="secondary-btn"
                :disabled="controlsLocked || previewLoading"
                @click="$emit('request-preview')"
              >
                <span v-if="previewLoading" class="spinner-sm"></span>
                {{ previewLoading ? $t('step1.generatingPreview') : $t('step1.previewBuildCost') }}
              </button>
              <button
                v-if="!isResearchMode"
                class="deep-research-btn"
                :disabled="controlsLocked"
                @click="toggleResearchMode"
              >
                🔍 {{ $t('step1.deepResearch') || 'Deep Research' }}
              </button>
              <button
                class="action-btn"
                :disabled="controlsLocked || previewLoading || !canConfirmBuild"
                @click="$emit('confirm-build')"
              >
                {{ $t('step1.confirmBuild') }}
              </button>
            </div>
          </div>

          <div v-if="currentPhase === 1 && buildProgress" class="progress-panel">
            <div class="progress-meta">
              <span>{{ buildProgress.message || $t('step1.buildInProgress') }}</span>
              <span>{{ buildProgress.progress || 0 }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${buildProgress.progress || 0}%` }"></div>
            </div>
          </div>

          <!-- Ontology Generation Loading State -->
          <div v-if="ontologyGenerating" class="ontology-generating-overlay">
            <div class="spinner-lg"></div>
            <span>{{ $t('step1.generatingOntologyFromText') || 'Generating ontology from research text...' }}</span>
          </div>

        <!-- Research Review Panel - visible when researchMode === 'deep' -->
          <div v-if="isResearchMode" class="research-panel">
            <div class="research-header">
              <span class="research-title">DEEP RESEARCH</span>
              <span v-if="hasResearchRun" class="research-badge" :class="researchStatusValue">
                {{ researchStatusValue.toUpperCase() }}
              </span>
            </div>

            <!-- Research not started -->
            <div v-if="!hasResearchRun" class="research-start">
              <p class="research-desc">Start deep research to analyze your documents with AI-powered search and synthesis.</p>
              <button class="action-btn" @click="handleStartResearch">
                Start Research
              </button>
            </div>

            <!-- Research pending/running -->
            <div v-else-if="isResearchPending || isResearchRunning" class="research-progress">
              <div class="spinner-sm"></div>
              <span>{{ researchStatus?.message || 'Processing research...' }}</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${researchStatus?.progress || 0}%` }"></div>
              </div>
            </div>

            <!-- Research completed - review state -->
            <div v-else-if="isResearchCompleted" class="research-review">
              <div v-if="researchResult?.markdown" class="research-result-preview">
                <span class="section-label">PREVIEW</span>
                <div class="markdown-preview" v-html="researchResult.markdown.substring(0, 500)"></div>
              </div>
              
              <div v-if="researchActionError" class="callout error">
                {{ researchActionError }}
              </div>

              <div class="research-actions">
                <button class="action-btn" @click="handleApproveResearch">
                  <Icon name="check" :size="14" /> Aprovar
                </button>
                <button class="secondary-btn" @click="handleRejectResearch">
                  ✗ Reject
                </button>
              </div>

              <div class="rerun-section">
                <span class="section-label">RERUN WITH FEEDBACK</span>
                <textarea 
                  v-model="rerunFeedback"
                  class="rerun-textarea"
                  placeholder="Enter feedback for improvement..."
                  rows="3"
                ></textarea>
                <button 
                  class="secondary-btn" 
                  :disabled="!rerunFeedback.trim()"
                  @click="handleRerunResearch"
                >
                  Rerun Research
                </button>
              </div>
            </div>

            <!-- Research approved - badge state -->
            <div v-else-if="isResearchApproved" class="research-approved">
              <span class="approval-badge"><Icon name="check" :size="14" /> APROVADO</span>
              <p>Research artifact has been approved and is ready for use.</p>
              
              <div class="promotion-section">
                <div v-if="promotionLoading" class="promotion-loading">
                  <div class="spinner-sm"></div>
                  <span>{{ promotionMessage || 'Processing...' }}</span>
                </div>
                <template v-else>
                  <button class="action-btn promote-btn" @click="handlePromoteResearch">
                    {{ $t('step1.useResearchForGraph') || 'usar isso para construir o grafo' }}
                  </button>
                </template>
              </div>
            </div>

            <!-- Research failed -->
            <div v-else-if="isResearchFailed" class="research-failed">
              <span class="failed-badge">✗ FAILED</span>
              <p>{{ researchStatus?.error || 'Research failed' }}</p>
              <button class="secondary-btn" @click="handleStartResearch">
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: currentPhase === 2, completed: currentPhase >= 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">{{ $t('step1.buildComplete') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase >= 2" class="badge accent">{{ $t('step1.inProgress') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/create</p>
          <p class="description">{{ $t('step1.buildCompleteDesc') }}</p>
          <button class="action-btn" :disabled="currentPhase < 2 || creatingSimulation" @click="handleEnterEnvSetup">
            <span v-if="creatingSimulation" class="spinner-sm"></span>
            {{ creatingSimulation ? $t('step1.creating') : `${$t('step1.enterEnvSetup')} ➝` }}
          </button>
        </div>
      </div>
    </div>

    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">{{ projectData?.project_id || 'NO_PROJECT' }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, index) in systemLogs" :key="index">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createSimulation } from '../api/simulation'
import { promoteResearch, createProjectFromResearch } from '../api/research'
import Icon from './Icon.vue'
import { getProfile } from '../store/pendingUpload.js'

const router = useRouter()
const { t } = useI18n()

const props = defineProps({
  currentPhase: { type: Number, default: 0 },
  projectData: Object,
  ontologyProgress: Object,
  buildProgress: Object,
  graphData: Object,
  chunkSize: { type: Number, default: 300 },
  chunkOverlap: { type: Number, default: 30 },
  costPreview: { type: Object, default: null },
  previewLoading: { type: Boolean, default: false },
  graphActionError: { type: String, default: '' },
  systemLogs: { type: Array, default: () => [] },
  // Research props
  researchMode: { type: String, default: 'basic' },
  researchStatus: { type: Object, default: null },
  researchResult: { type: Object, default: null },
  researchRunId: { type: String, default: null },
  researchActionError: { type: String, default: '' },
  ontologyGenerating: { type: Boolean, default: false }
})

const emit = defineEmits([
  'next-step', 
  'update-chunk-settings', 
  'request-preview', 
  'confirm-build',
  'enter-research-mode',
  'start-research',
  'approve-research',
  'reject-research',
  'rerun-research',
  'promote-success'
])

const selectedOntologyItem = ref(null)
const logContent = ref(null)
const creatingSimulation = ref(false)

const handleEnterEnvSetup = async () => {
  if (!props.projectData?.project_id || !props.projectData?.graph_id) {
    return
  }

  creatingSimulation.value = true

  try {
    const currentProfile = getProfile()
    const res = await createSimulation({
      project_id: props.projectData.project_id,
      graph_id: props.projectData.graph_id,
      enable_twitter: true,
      enable_reddit: true,
      profile: currentProfile
    })

    if (res.success && res.data?.simulation_id) {
      router.push({
        name: 'Simulation',
        params: { simulationId: res.data.simulation_id }
      })
      return
    }

    alert(t('step1.createSimulationFailed', { error: res.error || t('common.unknownError') }))
  } catch (err) {
    alert(t('step1.createSimulationException', { error: err.message }))
  } finally {
    creatingSimulation.value = false
  }
}

const selectOntologyItem = (item, type) => {
  selectedOntologyItem.value = { ...item, itemType: type }
}

const graphStats = computed(() => {
  const nodes = props.graphData?.node_count || props.graphData?.nodes?.length || 0
  const edges = props.graphData?.edge_count || props.graphData?.edges?.length || 0
  const types = props.projectData?.ontology?.entity_types?.length || 0
  return { nodes, edges, types }
})

const ontologyReady = computed(() => Boolean(props.projectData?.ontology))
const controlsLocked = computed(() => props.currentPhase > 0)
const previewReady = computed(() => Boolean(props.costPreview))
const ontologyGuardrails = computed(() => props.costPreview?.ontology_guardrails || null)
const canConfirmBuild = computed(() => Boolean(previewReady.value && ontologyGuardrails.value?.can_build !== false))

const updateChunk = (field, event) => {
  const value = event.target.valueAsNumber
  emit('update-chunk-settings', {
    chunkSize: field === 'chunkSize' ? value : props.chunkSize,
    chunkOverlap: field === 'chunkOverlap' ? value : props.chunkOverlap
  })
}

watch(() => props.systemLogs.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

// Research state
const rerunFeedback = ref('')
const promotionLoading = ref(false)
const promotionMessage = ref('')
const promotionError = ref('')

// Research computed
const isResearchMode = computed(() => props.researchMode === 'deep')
const hasResearchRun = computed(() => Boolean(props.researchRunId))
const researchStatusValue = computed(() => props.researchStatus?.status || 'none')
const isResearchPending = computed(() => researchStatusValue.value === 'pending')
const isResearchRunning = computed(() => researchStatusValue.value === 'running')
const isResearchCompleted = computed(() => researchStatusValue.value === 'completed')
const isResearchApproved = computed(() => researchStatusValue.value === 'approved')
const isResearchFailed = computed(() => researchStatusValue.value === 'failed')

// Research actions
const toggleResearchMode = () => {
  emit('enter-research-mode')
}

const handleStartResearch = () => {
  const query = props.projectData?.name || 'Research query'
  emit('start-research', query)
}

const handleApproveResearch = () => {
  emit('approve-research')
}

const handleRejectResearch = () => {
  emit('reject-research')
}

const handleRerunResearch = () => {
  if (!rerunFeedback.value.trim()) return
  emit('rerun-research', rerunFeedback.value)
  rerunFeedback.value = ''
}

const handlePromoteResearch = async () => {
  if (!props.researchRunId) return
  
  promotionLoading.value = true
  promotionMessage.value = ''
  promotionError.value = ''
  
  try {
    let result
    
    // Check if project already exists - if so, promote; otherwise create new project
    if (props.projectData?.project_id) {
      // Project exists - promote research to it
      promotionMessage.value = 'Promoting research to project...'
      result = await promoteResearch(props.researchRunId, props.projectData.project_id)
    } else {
      // No project - create from research
      promotionMessage.value = 'Creating project from research...'
      result = await createProjectFromResearch(props.researchRunId)
    }
    
    if (result.success) {
      promotionMessage.value = 'Success!'
      emit('promote-success', result.data)
    } else {
      promotionError.value = result.error || 'Promotion failed'
    }
  } catch (err) {
    promotionError.value = err.message || 'An error occurred'
  } finally {
    // Clear message after a short delay
    setTimeout(() => {
      promotionLoading.value = false
      promotionMessage.value = ''
    }, 2000)
  }
}
</script>

<style scoped>
.workbench-panel {
  height: 100%;
  background-color: var(--color-surface-container-low);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-card {
  background: var(--color-surface-container-highest);
  border-radius: 0;
  padding: 20px;
  border: none;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
}

.step-card.active {
  border: 2px solid var(--profile-primary, var(--color-on-background));
  box-shadow: 4px 4px 0 var(--profile-primary, var(--color-on-background));
  transform: translate(-2px, -2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-outline);
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: var(--color-on-background);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.5px;
}

.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.success {
  background: rgba(46, 125, 50, 0.15);
  color: var(--color-success, var(--color-success));
}

.badge.processing,
.badge.accent {
  background: var(--profile-primary, var(--color-error));
  color: var(--color-on-primary, var(--color-surface));
}

.badge.pending {
  background: var(--color-surface-container-highest, var(--color-surface-container-low));
  color: var(--color-outline, var(--color-disabled));
}

.badge.error {
  background: rgba(186, 26, 26, 0.15);
  color: var(--color-error, var(--color-error));
}

.api-note {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--color-disabled);
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.5;
  margin-bottom: 16px;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--profile-primary, var(--color-error));
  margin-bottom: 12px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid var(--profile-light, var(--color-warning-bg));
  border-top-color: var(--profile-primary, #FF5722);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.tags-container {
  margin-top: 12px;
  transition: opacity 0.3s;
}

.tags-container.dimmed {
  opacity: 0.3;
  pointer-events: none;
}

.tag-label {
  display: block;
  font-size: 10px;
  color: var(--color-disabled);
  margin-bottom: 8px;
  font-weight: 600;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--color-on-surface);
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.2s;
}

.entity-tag.clickable {
  cursor: pointer;
}

.entity-tag.clickable:hover {
  background: var(--color-outline);
  border-color: var(--color-outline);
}

.ontology-detail-overlay {
  position: absolute;
  top: 60px;
  left: 20px;
  right: 20px;
  bottom: 20px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(4px);
  z-index: 10;
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-container-low);
}

.detail-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-type-badge {
  font-size: 9px;
  font-weight: 700;
  color: var(--color-surface);
  background: var(--color-on-background);
  padding: 2px 6px;
  border-radius: 2px;
  text-transform: uppercase;
}

.detail-name {
  font-size: 14px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--color-disabled);
  cursor: pointer;
  line-height: 1;
  border-radius: 0;
}

.close-btn:hover {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.detail-desc {
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.5;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--color-outline);
}

.detail-section {
  margin-bottom: 16px;
}

.section-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-disabled);
  margin-bottom: 8px;
}

.attr-list,
.conn-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attr-item {
  font-size: 11px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
  padding: 4px;
  background: var(--color-background);
  border-radius: 4px;
}

.attr-name {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: var(--color-on-background);
}

.attr-type {
  color: var(--color-disabled);
  font-size: 10px;
}

.attr-desc {
  color: var(--color-muted);
  flex: 1;
  min-width: 150px;
}

.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.example-tag {
  font-size: 11px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: 3px 8px;
  border-radius: 12px;
  color: var(--color-muted);
}

.conn-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 6px;
  background: var(--color-surface-container-low);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.conn-node {
  font-weight: 600;
  color: var(--color-on-surface);
}

.conn-arrow {
  color: var(--color-disabled);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  background: var(--color-background);
  padding: 16px;
  border-radius: 6px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-background);
  font-family: 'JetBrains Mono', monospace;
}

.stat-label {
  font-size: 9px;
  color: var(--color-disabled);
  text-transform: uppercase;
  margin-top: 4px;
  display: block;
}

.control-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--color-muted);
  text-transform: uppercase;
}

.field-input {
  width: 100%;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  padding: 10px 12px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-on-background);
}

.field-hint {
  font-size: 10px;
  color: var(--color-muted);
  line-height: 1.4;
}

.callout {
  margin-top: 16px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  border-radius: 6px;
}

.callout.neutral {
  background: var(--color-surface-container-low);
  color: var(--color-muted);
}

.callout.error {
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error-bg);
}

.action-stack {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.button-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.preview-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  padding: 14px;
}

.preview-card.warning {
  border-color: #F0B273;
  background: var(--color-warning-bg);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface);
}

.preview-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 999px;
}

.preview-pill.safe {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.preview-pill.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.guardrail-card {
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning);
  border-radius: 6px;
  padding: 14px;
}

.guardrail-card.blocking {
  background: var(--color-error-bg);
  border-color: #F3C5BF;
}

.guardrail-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.guardrail-title,
.guardrail-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-on-surface);
  text-transform: uppercase;
}

.guardrail-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 999px;
}

.guardrail-pill.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.guardrail-pill.blocking {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.guardrail-group + .guardrail-group {
  margin-top: 12px;
}

.guardrail-list {
  margin: 8px 0 0;
  padding-left: 18px;
  color: var(--color-muted);
  font-size: 12px;
  line-height: 1.5;
}

.preview-stat {
  background: var(--color-background);
  border-radius: 6px;
  padding: 12px;
  min-height: 72px;
}

.preview-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-on-background);
}

.preview-label {
  display: block;
  margin-top: 6px;
  font-size: 10px;
  color: var(--color-muted);
  text-transform: uppercase;
}

.secondary-btn,
.action-btn {
  width: 100%;
  background: var(--color-on-background);
  color: var(--color-surface-container-highest);
  border: none;
  padding: 14px;
  border-radius: 0;
  font-size: 12px;
  font-family: var(--font-machine);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn {
  background: var(--color-surface-container-low);
  color: var(--color-on-background);
  border: 1px solid var(--color-outline);
}

.secondary-btn:hover:not(:disabled),
.action-btn:hover:not(:disabled) {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.secondary-btn:disabled,
.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.deep-research-btn {
  width: 100%;
  background: var(--color-surface);
  color: var(--color-surface-container-highest);
  border: 1px solid var(--color-surface-elevated);
  padding: 14px;
  border-radius: 0;
  font-size: 12px;
  font-family: var(--font-machine);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.deep-research-btn:hover:not(:disabled) {
  background: var(--color-surface-elevated);
  box-shadow: 4px 4px 0 var(--color-surface-elevated);
}

.deep-research-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.progress-panel {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--color-muted);
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: var(--color-surface-container-highest, var(--color-surface-container-low));
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--profile-primary, #FF5722) 0%, var(--profile-accent, #FF8A65) 100%);
  transition: width 0.2s ease;
}

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
  height: 80px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: var(--color-on-surface);
  border-radius: 2px;
}

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time {
  color: var(--color-muted);
  min-width: 75px;
}

.log-msg {
  color: var(--color-outline);
  word-break: break-all;
}

/* Research Panel */
.research-panel {
  margin-top: 20px;
  padding: 16px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

.research-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.research-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-background);
  letter-spacing: 1px;
}

.research-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  text-transform: uppercase;
}

.research-badge.pending,
.research-badge.running {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.research-badge.completed {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.research-badge.approved {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.research-badge.failed {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.research-start {
  text-align: center;
  padding: 20px 0;
}

.research-desc {
  font-size: 12px;
  color: var(--color-muted);
  margin-bottom: 16px;
}

.research-progress {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  padding: 20px 0;
}

.research-progress .spinner-sm {
  width: 24px;
  height: 24px;
  border-width: 3px;
}

.research-review {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.research-result-preview {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: 12px;
  border-radius: 4px;
}

.markdown-preview {
  font-size: 11px;
  color: var(--color-muted);
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  margin-top: 8px;
}

.research-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.rerun-section {
  border-top: 1px solid var(--color-outline);
  padding-top: 16px;
}

.rerun-textarea {
  width: 100%;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  padding: 10px 12px;
  font-size: 12px;
  font-family: inherit;
  color: var(--color-on-background);
  resize: vertical;
  min-height: 60px;
  margin: 8px 0;
  border-radius: 4px;
}

.rerun-textarea:focus {
  outline: none;
  border-color: var(--color-on-background);
}

.research-approved {
  text-align: center;
  padding: 20px 0;
}

.approval-badge {
  display: inline-block;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-success);
  background: var(--color-success-bg);
  padding: 8px 16px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.research-approved p {
  font-size: 12px;
  color: var(--color-muted);
}

.promotion-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-outline);
}

.promotion-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--color-muted);
  font-size: 12px;
}

.promote-btn {
  width: 100%;
  background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%);
  color: var(--color-surface);
  font-weight: 700;
}

.promote-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #388E3C 0%, #2E7D32 100%);
  box-shadow: 4px 4px 0 var(--color-success);
}

.research-failed {
  text-align: center;
  padding: 20px 0;
}

.failed-badge {
  display: inline-block;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-error);
  background: var(--color-error-bg);
  padding: 8px 16px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.research-failed p {
  font-size: 12px;
  color: var(--color-muted);
  margin-bottom: 16px;
}

.ontology-generating-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 20;
  border-radius: inherit;
}

.ontology-generating-overlay span {
  font-size: 14px;
  color: var(--color-muted);
  font-weight: 500;
}

.spinner-lg {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-warning-bg);
  border-top-color: #FF5722;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@media (max-width: 768px) {
  .card-header,
  .preview-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid,
  .control-grid,
  .button-row,
  .preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>

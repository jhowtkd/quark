<template>
  <div class="process-page">
    <!-- Controlador de Topo -->
    <nav class="navbar">
      <div class="nav-brand" @click="goHome">FUTUR.IA</div>
      
      <!-- Indicador central de estágio -->
      <div class="nav-center">
        <div class="step-badge">STEP 01</div>
        <div class="step-name">Construir Grafo</div>
      </div>

      <div class="nav-status">
        <ThemeToggle />
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </nav>

    <!-- Área Principal Box -->
    <div class="main-content">
      <!-- Esquerda: Render do Graph -->
      <div class="left-panel" :class="{ 'full-screen': isFullScreen }">
        <div class="panel-header">
          <div class="header-left">
            <Icon name="diamond" :size="14" class="header-deco" />
            <span class="header-title">Grafo de Conhecimento</span>
          </div>
          <div class="header-right">
            <template v-if="graphData">
              <span class="stat-item">{{ graphData.node_count || graphData.nodes?.length || 0 }} nós</span>
              <span class="stat-divider">|</span>
              <span class="stat-item">{{ graphData.edge_count || graphData.edges?.length || 0 }} relações</span>
              <span class="stat-divider">|</span>
            </template>
            <div class="action-buttons">
                <button class="action-btn" @click="refreshGraph" :disabled="graphLoading" title="Atualizar grafo">
                  <Icon name="refresh-cw" :size="16" :class="{ 'spinning': graphLoading }" />
                </button>
                <button class="action-btn" @click="toggleFullScreen" :title="isFullScreen ? 'Sair da tela cheia' : 'Mostrar em tela cheia'">
                  <Icon :name="isFullScreen ? 'minimize-2' : 'maximize-2'" :size="16" />
                </button>
            </div>
          </div>
        </div>
        
        <div class="graph-container" ref="graphContainer">
          <!-- Viewer Box Canvas -->
          <div v-if="graphData" class="graph-view">
            <svg ref="graphSvg" class="graph-svg"></svg>
            <!-- Alerta de Processos BG -->
            <div v-if="currentPhase === 1" class="graph-building-hint">
              <span class="building-dot"></span>
              Atualizando em tempo real...
            </div>
            
            <!-- Box Info Node D3 -->
            <div v-if="selectedItem" class="detail-panel">
              <div class="detail-panel-header">
                <span class="detail-title">{{ selectedItem.type === 'node' ? 'Node Details' : 'Relationship' }}</span>
                <span v-if="selectedItem.type === 'node'" class="detail-badge" :style="{ background: selectedItem.color }">
                  {{ selectedItem.entityType }}
                </span>
                <button class="detail-close" @click="closeDetailPanel"><Icon name="x" :size="16" /></button>
              </div>
              
              <!-- Inner Div Props Node -->
              <div v-if="selectedItem.type === 'node'" class="detail-content">
                <div class="detail-row">
                  <span class="detail-label">Name:</span>
                  <span class="detail-value highlight">{{ selectedItem.data.name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Created:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                
                <!-- Properties / Attributes -->
                <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
                  <span class="detail-label">Properties:</span>
                  <div class="properties-list">
                    <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                      <span class="property-key">{{ key }}:</span>
                      <span class="property-value">{{ value }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Summary -->
                <div class="detail-section" v-if="selectedItem.data.summary">
                  <span class="detail-label">Summary:</span>
                  <p class="detail-summary">{{ selectedItem.data.summary }}</p>
                </div>
                
                <!-- Labels -->
                <div class="detail-row" v-if="selectedItem.data.labels?.length">
                  <span class="detail-label">Labels:</span>
                  <div class="detail-labels">
                    <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">{{ label }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Inner Div Props Link -->
              <div v-else class="detail-content">
                <!-- Inner Label Link -->
                <div class="edge-relation">
                  <span class="edge-source">{{ selectedItem.data.source_name || selectedItem.data.source_node_name }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-type">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-target">{{ selectedItem.data.target_name || selectedItem.data.target_node_name }}</span>
                </div>
                
                <div class="detail-subtitle">Relationship</div>
                
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Label:</span>
                  <span class="detail-value">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.fact_type">
                  <span class="detail-label">Type:</span>
                  <span class="detail-value">{{ selectedItem.data.fact_type }}</span>
                </div>
                
                <!-- Fact -->
                <div class="detail-section" v-if="selectedItem.data.fact">
                  <span class="detail-label">Fact:</span>
                  <p class="detail-summary">{{ selectedItem.data.fact }}</p>
                </div>
                
                <!-- Episodes -->
                <div class="detail-section" v-if="selectedItem.data.episodes?.length">
                  <span class="detail-label">Episodes:</span>
                  <div class="episodes-list">
                    <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">{{ ep }}</span>
                  </div>
                </div>
                
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Created:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.valid_at">
                  <span class="detail-label">Valid From:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.valid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.invalid_at">
                  <span class="detail-label">Invalid At:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.invalid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.expired_at">
                  <span class="detail-label">Expired At:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.expired_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Loading Global -->
          <div v-else-if="graphLoading" class="graph-loading">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="loading-text">Carregando dados do grafo...</p>
          </div>
          
          <!-- Queue Base Esperando Status -->
          <div v-else-if="currentPhase < 1" class="graph-waiting">
            <div class="waiting-icon">
              <svg viewBox="0 0 100 100" class="network-icon">
                <circle cx="50" cy="20" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="20" cy="60" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="80" cy="60" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="50" cy="80" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <line x1="50" y1="28" x2="25" y2="54" stroke="#000" stroke-width="1"/>
                <line x1="50" y1="28" x2="75" y2="54" stroke="#000" stroke-width="1"/>
                <line x1="28" y1="60" x2="72" y2="60" stroke="#000" stroke-width="1" stroke-dasharray="4"/>
                <line x1="50" y1="72" x2="26" y2="66" stroke="#000" stroke-width="1"/>
                <line x1="50" y1="72" x2="74" y2="66" stroke="#000" stroke-width="1"/>
              </svg>
            </div>
            <p class="waiting-text">And Then List Continue End Array Spread Iteration Wait Elements UI Next Data Items Rest Remaining Others List Objects Result Output Next Setup Vue Components Display Values Arrays Data Binding Scope Value Items待Gerar Ontologia</p>
            <p class="waiting-hint">O grafo será construído automaticamente após gerar</p>
          </div>
          
          <!-- Processing DB Block -->
          <div v-else-if="currentPhase === 1 && !graphData" class="graph-waiting">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="waiting-text">Construir Grafo中</p>
            <p class="waiting-hint">Dados aparecerão em breve...</p>
          </div>
          
          <!-- Errors Catching Visor Box Red -->
          <div v-else-if="error" class="graph-error">
            <span class="error-icon">⚠</span>
            <p>{{ error }}</p>
          </div>
        </div>
        
        <!-- Legends Box Floating Render -->
        <div v-if="graphData" class="graph-legend">
          <div class="legend-item" v-for="type in entityTypes" :key="type.name">
            <span class="legend-dot" :style="{ background: type.color }"></span>
            <span class="legend-label">{{ type.name }}</span>
            <span class="legend-count">{{ type.count }}</span>
          </div>
        </div>
      </div>

      <!-- Right Base Pipeline Info Flow Steps -->
      <div class="right-panel" :class="{ 'hidden': isFullScreen }">
        <div class="panel-header dark-header">
          <span class="header-icon">▣</span>
          <span class="header-title">Processo de Construção</span>
        </div>

        <div class="process-content">
          <!-- Fase1: Gerar Ontologia -->
          <div class="process-phase" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
            <div class="phase-header">
              <span class="phase-num">01</span>
              <div class="phase-info">
                <div class="phase-title">Gerar Ontologia</div>
                <div class="phase-api">/api/graph/ontology/generate</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(0)">
                {{ getPhaseStatusText(0) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">Descrição</div>
                <div class="detail-content">
                  After Process Sync File Buffer Event Send Payload Render Format String Formats Check Fetch Check Setup Pattern Event Execute Variable Props Target Fetch Variables Flow Displays Execution Return Check Run Displays Pattern Outputs Returns Displays Methods Match Displays Returns Execution Map Method Mapping Execution Values Match String，LLMAnalisando conteúdo...，Generative Layout AI Based Structuring Setup Ontology Graph Data Build Automap Execute Event String Scope Formatting Render Variables Mapping Process Match Run Return Prop Check Output Call View（Tipos + relaçõesTipo da Entidade）
                </div>
              </div>
              
              <!-- Gerar OntologiaAndamento % -->
              <div class="detail-section" v-if="ontologyProgress && currentPhase === 0">
                <div class="detail-label">Progresso</div>
                <div class="ontology-progress">
                  <div class="progress-spinner"></div>
                  <span class="progress-text">{{ ontologyProgress.message }}</span>
                </div>
              </div>
              
              <!-- Ontol Load Info Labels Box -->
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">Entidades geradas ({{ projectData.ontology.entity_types?.length || 0 }})</div>
                <div class="entity-tags">
                  <span 
                    v-for="entity in projectData.ontology.entity_types" 
                    :key="entity.name"
                    class="entity-tag"
                  >
                    {{ entity.name }}
                  </span>
                </div>
              </div>
              
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">Matriz das Relações Extraídas Criadas ({{ projectData.ontology.relation_types?.length || 0 }})</div>
                <div class="relation-list">
                  <div 
                    v-for="(rel, idx) in projectData.ontology.relation_types?.slice(0, 5) || []" 
                    :key="idx"
                    class="relation-item"
                  >
                    <span class="rel-source">{{ rel.source_type }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-name">{{ rel.name }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-target">{{ rel.target_type }}</span>
                  </div>
                  <div v-if="(projectData.ontology.relation_types?.length || 0) > 5" class="relation-more">
                    +{{ projectData.ontology.relation_types.length - 5 }} Ver Restante (+)relações...
                  </div>
                </div>
              </div>
              
              <!-- Wait Check -->
              <div class="detail-section waiting-state" v-if="!projectData?.ontology && currentPhase === 0 && !ontologyProgress">
                <div class="waiting-hint">Gerando base de esquema RAG...</div>
              </div>
            </div>
          </div>

          <!-- Fase2: Construir Grafo -->
          <div class="process-phase" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
            <div class="phase-header">
              <span class="phase-num">02</span>
              <div class="phase-info">
                <div class="phase-title">Construir Grafo</div>
                <div class="phase-api">/api/graph/build</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(1)">
                {{ getPhaseStatusText(1) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">Descrição</div>
                <div class="detail-content">
                  From Ontology Extract Call Zep Graph Build Connect Entities Extract Scope Output Exec Layout Formatting Arrays Value Displays Method Formats Target Outputs Results Code Call Outputs Render Formats Object Setup Object Execute Action Execution Event Target String Process Loop Results Match Handling Methods Arrays Check Check Action Rendering Functions Code Scope Returnrelações
                </div>
              </div>
              
              <!-- Ontol Check Process -->
              <div class="detail-section waiting-state" v-if="currentPhase < 1">
                <div class="waiting-hint">Fechando extrações...</div>
              </div>
              
              <!-- Status -->
              <div class="detail-section" v-if="buildProgress && currentPhase >= 1">
                <div class="detail-label">Status</div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: buildProgress.progress + '%' }"></div>
                </div>
                <div class="progress-info">
                  <span class="progress-message">{{ buildProgress.message }}</span>
                  <span class="progress-percent">{{ buildProgress.progress }}%</span>
                </div>
              </div>
              
              <div class="detail-section" v-if="graphData">
                <div class="detail-label">Resultados</div>
                <div class="build-result">
                  <div class="result-item">
                    <span class="result-value">{{ graphData.node_count }}</span>
                    <span class="result-label">Identidadenós</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ graphData.edge_count }}</span>
                    <span class="result-label">relaçõesEdge Connect</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ entityTypes.length }}</span>
                    <span class="result-label">Tipos</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Fase3: 完成 -->
          <div class="process-phase" :class="{ 'active': currentPhase === 2, 'completed': currentPhase > 2 }">
            <div class="phase-header">
              <span class="phase-num">03</span>
              <div class="phase-info">
                <div class="phase-title">Concluído</div>
                <div class="phase-api">Preparar para continuar</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(2)">
                {{ getPhaseStatusText(2) }}
              </span>
            </div>
          </div>

          <!-- Avançar Botão Box -->
          <div class="next-step-section" v-if="currentPhase >= 2">
            <button class="next-step-btn" @click="goToNextStep" :disabled="currentPhase < 2">
              Ir para Configuração do Ambiente
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>

        <!-- Panel Specs Base Vars Info Values -->
        <div class="project-panel">
          <div class="project-header">
            <span class="project-icon">◇</span>
            <span class="project-title">Projeto</span>
          </div>
          <div class="project-details" v-if="projectData">
            <div class="project-item">
              <span class="item-label">Nome</span>
              <span class="item-value">{{ projectData.name }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">ID</span>
              <span class="item-value code">{{ projectData.project_id }}</span>
            </div>
            <div class="project-item" v-if="projectData.graph_id">
              <span class="item-label">Grafo ID</span>
              <span class="item-value code">{{ projectData.graph_id }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">Alvo Base</span>
              <span class="item-value">{{ projectData.simulation_requirement || '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { generateOntology, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'
import ThemeToggle from '../components/ThemeToggle.vue'
import Icon from '../components/Icon.vue'
import * as d3 from 'd3'

const route = useRoute()
const router = useRouter()

// Id Base Context Flow Variables Pattern Target Event Object Execution Object Mapping Action Arrays Handle Flow Props Array Map Code Output Model Scope Displays Process Result Output Run Methods Results Functions Response Regex Method Array View'new'Param Id Change Actual To Fixed Virtual New Route Controller ID Assign Base Prop Update Var State Change Real ValueID）
const currentProjectId = ref(route.params.projectId)

// 状态
const loading = ref(true)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const buildProgress = ref(null)
const ontologyProgress = ref(null) // Gerar OntologiaAndamento %
const currentPhase = ref(-1) // -1: Recebendo Volume HTTP..., 0: Gerar Ontologia中, 1: Construir Grafo, 2: 完成
const selectedItem = ref(null) // InFocus ObjnósLink Edges Target Schema Info Box Model Component Layout Result Logic Execution Code Return Layout Return Method Formats Match Variables Action Return
const isFullScreen = ref(false)


// DOMReferência Pointer
const graphContainer = ref(null)
const graphSvg = ref(null)

// Loops JS setInterval.
let pollTimer = null

// Computados dinâmicos
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return 'Build Broken Server Fallback.'
  if (currentPhase.value >= 2) return 'Concluído'
  if (currentPhase.value === 1) return 'Construir Grafo中'
  if (currentPhase.value === 0) return 'Gerar Ontologia中'
  return 'Inicializando...'
})

const entityTypes = computed(() => {
  if (!graphData.value?.nodes) return []
  
  const typeMap = {}
  const colors = ['#FF6B35', '#004E89', '#7B2D8E', '#1A936F', '#C5283D', '#E9724C']
  
  graphData.value.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || 'Entity'
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  
  return Object.values(typeMap)
})

// Actions e Mutations Block Control Flow Methods.
const goHome = () => {
  router.push('/')
}

const goToNextStep = () => {
  // TODO: Ir para Configuração do AmbientePasso X
  alert('Not Implemented View Feature / Soon....')
}

const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  // Wait for transition to finish then re-render graph
  setTimeout(() => {
    renderGraph()
  }, 350) 
}

// Botão de Ocultar Visor de Dados Box
const closeDetailPanel = () => {
  selectedItem.value = null
}

// Date Str Formatter
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('pt-BR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// Selected Layout Formatting Formats Run Flow Check Arrays Variables String Return Display Properties Map Setup Render Output Action Control Outputs Variable Formats Output Fetch Layout Method Mapping Process Call Formats Values Format Method Handling Results Method Display Handle Methods Flow Displays Outputs Returns Check Response Functionnós
const selectNode = (nodeData, color) => {
  selectedItem.value = {
    type: 'node',
    data: nodeData,
    color: color,
    entityType: nodeData.labels?.find(l => l !== 'Entity' && l !== 'Node') || 'Entity'
  }
}

// Select Edge Click Visual Pointer Events
const selectEdge = (edgeData) => {
  selectedItem.value = {
    type: 'edge',
    data: edgeData
  }
}

const getPhaseStatusClass = (phase) => {
  if (currentPhase.value > phase) return 'completed'
  if (currentPhase.value === phase) return 'active'
  return 'pending'
}

const getPhaseStatusText = (phase) => {
  if (currentPhase.value > phase) return 'Terminado'
  if (currentPhase.value === phase) {
    if (phase === 1 && buildProgress.value) {
      return `${buildProgress.value.progress}%`
    }
    return 'Em andamento'
  }
  return 'Aguardando'
}

// 初始化 - Handle New Creates Upload POST Rest Project Init.VersoCarregar projeto existente
const initProject = async () => {
  const paramProjectId = route.params.projectId
  
  if (paramProjectId === 'new') {
    // Store Use Local Fetch Init Base Data Payload
    await handleNewProject()
  } else {
    // Carregar projeto existente
    currentProjectId.value = paramProjectId
    await loadProject()
  }
}

// Handle New Creates Upload POST Rest Project Init. - Caller Func ontology/generate API
const handleNewProject = async () => {
  const pending = getPendingUpload()
  
  if (!pending.isPending || pending.files.length === 0) {
    error.value = 'Nenhum arquivo. Volte para a página principal'
    loading.value = false
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0 // Gerar OntologiaFase
    ontologyProgress.value = { message: 'Enviando arquivo e analisando documento...' }
    
    // Construir DB FormData
    const formDataObj = new FormData()
    pending.files.forEach(file => {
      formDataObj.append('files', file)
    })
    formDataObj.append('simulation_requirement', pending.simulationRequirement)
    
    // Caller FuncGerar Ontologia API
    const response = await generateOntology(formDataObj)
    
    if (response.success) {
      // Clear Memory Cache Local Var Project Unlinked
      clearPendingUpload()
      
      // Overwrite Target Id Data Array Logic Execution Results String Process Fetch Render Fetch Component Result Execute Target Regex Action Output Setup Objects Pattern Output Execute Component View Fetch Object Output Formats Handling Result Properties
      currentProjectId.value = response.data.project_id
      projectData.value = response.data
      
      // Update history Router Vue push id not refresh windows hard limit state）
      router.replace({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
      
      ontologyProgress.value = null
      
      // Hook Automático Target State Component Prop Call View Variable Execution Event Regex Display Map Displays Call Return Loop Function Function Render Formats String Output Flow Component Output Match Array Functions Returns Value Outputs Object Code Variables Result Formatting Object Arrays Setup Pattern FetchConstruir Grafo
      await startBuildGraph()
    } else {
      error.value = response.error || 'Gerar OntologiaError Catch Target Map Array Formatting Flow Maps Action Check Displays Displays Setup Values Values Flow Output Response Return Methods Regex Variable Setup Execute Component String Map Logic Mapping Outputs String Output'
    }
  } catch (err) {
    // DEBUG: Handle new project error
    error.value = 'Falha ao inicializar projeto: ' + (err.message || 'Desconhecimento API ERROR...')
  } finally {
    loading.value = false
  }
}

// Carregar projeto existenteLogs JSON
const loadProject = async () => {
  try {
    loading.value = true
    const response = await getProject(currentProjectId.value)
    
    if (response.success) {
      projectData.value = response.data
      updatePhaseByStatus(response.data.status)
      
      // Hook Automático Target State Component Prop Call View Variable Execution Event Regex Display Map Displays Call Return Loop Function Function Render Formats String Output Flow Component Output Match Array Functions Returns Value Outputs Object Code Variables Result Formatting Object Arrays Setup Pattern FetchConstruir Grafo
      if (response.data.status === 'ontology_generated' && !response.data.graph_id) {
        await startBuildGraph()
      }
      
      // Polling persistente liberado task bg.
      if (response.data.status === 'graph_building' && response.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(response.data.graph_build_task_id)
      }
      
      // Fetch Finish Graph Layout Render Map Outputs Displays Handling Output Handle Mapping Call Method Prop Target Formats Returns Method Scope Variable Process Results App Action Output Display Logic Variable Fetch Regex Object Variables Regex Handle Displays Code Check Control Fetch Displays Setup Target Component Setup Action Outputs Format Setup Output Props Action Component Function Return Setup Maps Value Layout Formatting Code Flow Execute Scope Display Mapping Flow Displays Mapping Outputs Variables
      if (response.data.status === 'graph_completed' && response.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(response.data.graph_id)
      }
    } else {
      error.value = response.error || 'Falha ao carregar projeto'
    }
  } catch (err) {
    // DEBUG: Load project error
    error.value = 'Falha ao carregar projeto: ' + (err.message || 'Desconhecimento API ERROR...')
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated':
      currentPhase.value = 0
      break
    case 'graph_building':
      currentPhase.value = 1
      break
    case 'graph_completed':
      currentPhase.value = 2
      break
    case 'failed':
      error.value = projectData.value?.error || 'Processamento falhou'
      break
  }
}

// START GRAPH BUILD BATCH.
const startBuildGraph = async () => {
  try {
    currentPhase.value = 1
    // Initial Var Perc = 0.
    buildProgress.value = {
      progress: 0,
      message: 'Inicializando...Construir Grafo...'
    }
    
    const response = await buildGraph({ project_id: currentProjectId.value })
    
    if (response.success) {
      buildProgress.value.message = 'Construir GrafoSchedule Success Flow Method Maps Scope Output Return State Action Prop Formatting Outputs Methods Display View Values Method Display Return Run Rendering Method Arrays Fetch Logic Formatting Process Regex Formats Formatting Handle Array Format Outputs Call Component Display String Variables Target Exec App Outputs Code Return Result Map Return Setup Method Handle Control Action Output Output...'
      
      // Salvar Params. task_id Usage Poll Var Logic Controller Interval State Update Loop Background Async
      const taskId = response.data.task_id
      
      // Polled Timer Para Graph BD（Self Polling Loop Control Logic Target Map Formats Variables Mapping Returns Component Control Setup Flow Display Handling Display Code Result Method Map Results Check Return Flow Mapping Formats Action Return Control Result Handling Returns Map Handle Target Properties Result Results Mapping Action Format String Control Map Methods Variables Displays Fetch Functions Display）
      startGraphPolling()
      
      // Start Loop Timer ID Thread JS Window To API Get.
      startPollingTask(taskId)
    } else {
      error.value = response.error || 'Zep Create Error Method Display Event State Result Code Result Methods Mapping Output Run Execute Arrays Setup Data Display Fetch Values Method Displays Object Arrays Value Layout Handle Array Result Displays Output Displays Component Variables Prop Code Run Return Call Target Method Action Handling Properties Formatting Object State Formats Array Logic Process Output'
      buildProgress.value = null
    }
  } catch (err) {
    // DEBUG: Build graph error
    error.value = 'Zep Create Error Method Display Event State Result Code Result Methods Mapping Output Run Execute Arrays Setup Data Display Fetch Values Method Displays Object Arrays Value Layout Handle Array Result Displays Output Displays Component Variables Prop Code Run Return Call Target Method Action Handling Properties Formatting Object State Formats Array Logic Process Output: ' + (err.message || 'Desconhecimento API ERROR...')
    buildProgress.value = null
  }
}

// Interval Logic For BD Node Sync Fetch Graph Data Async Promises Get
let graphPollTimer = null

// Polled Timer Para Graph BD
const startGraphPolling = () => {
  // Load único prioritário
  fetchGraphData()
  
  // 10s Poll Timer BG Fetch Graph...
  graphPollTimer = setInterval(async () => {
    await fetchGraphData()
  }, 10000)
}

// Manualmente Button Interv. Execution Return Scope Code Outputs Logic Flow Results Component Function Map Result Handling Formats Array Formats Target View Check Object Logic Arrays Outputs Variable Output Format Action Return Exec Map Props MapAtualizar grafo
const refreshGraph = async () => {
  graphLoading.value = true
  await fetchGraphData()
  graphLoading.value = false
}

// Clear Interval BD Memory ID Stop Loops Check Timer Poll Logic Exit Clean Break Return Function Method
const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
  }
}

// Scope Results Handle Process Displays Output Loop Object Run Outputs Layout Map Props Response Components Target Formats Values Result Fetch Event Handling Flow Arrays Method Formats Display Action Regex Target Components Match Arrays Fetch Variable Variables Outputs Result Run Arrays Output Results Methods Logic State Display Outputs Output Map Layout Process Values Handle String Value Flow Exec Logic Action Method Output Object Call State Regex Fetch View Methods Execute Arrays Setup Result Display Object Returns Control Results Returns Fetch Value Pattern Mapping Action Output Action Method Handling Logic App Formatting Value Prop Results Handling Control Arrays Outputs Scope Execute Function Match Handling View Output Handling Method Check View Object Code Method Formats Variable Execution Exec Component Map Variable Method Setup Variables Format Code Execute Formatting Output Returns Run Formats Process Check Props Methods Action Result Logic Result Display Action Logic Return Flow Formats Handle Props Exec Display Regex Logic Function Functions Target Layout View Output Control Execute Call Data Fetch Action Execution Check Properties Outputs Returns Output Method Object Execution Target Check Functions Match Array Execute Props Control Formats Map Properties Return Variable Handling Process Return Formats Layout Object Object Setup Variables Function Layout Arrays Formatting Props Maps Code Execution Return Action Run Properties Functions Arrays Mapping Rendering Outputs Value Returns Pattern Variables Outputs Scope String Components Prop
const fetchGraphData = async () => {
  try {
    // Busca ID Primary Key Project Get Meta Call Exec Arrays Render Displays Results Value Regex Component Variables Value Control Returns Flow Control Logic Properties Mapping Props Execute Arrays Results Displays Return Action Maps Handling Action Call Mapping Handle Formats Code Formats Response Formatting Fetch Result Control Code Output graph_id
    const projectResponse = await getProject(currentProjectId.value)
    
    if (projectResponse.success && projectResponse.data.graph_id) {
      const graphId = projectResponse.data.graph_id
      projectData.value = projectResponse.data
      
      // Scope Results Handle Process Displays Output Loop Object Run Outputs Layout Map Props Response Components Target Formats Values Result Fetch Event Handling Flow Arrays Method Formats Display Action Regex Target Components Match Arrays Fetch Variable Variables Outputs Result Run Arrays Output Results Methods Logic State Display Outputs Output Map Layout Process Values Handle String Value Flow Exec Logic Action Method Output Object Call State Regex Fetch View Methods Execute Arrays Setup Result Display Object Returns Control Results Returns Fetch Value Pattern Mapping Action Output Action Method Handling Logic App Formatting Value Prop Results Handling Control Arrays Outputs Scope Execute Function Match Handling View Output Handling Method Check View Object Code Method Formats Variable Execution Exec Component Map Variable Method Setup Variables Format Code Execute Formatting Output Returns Run Formats Process Check Props Methods Action Result Logic Result Display Action Logic Return Flow Formats Handle Props Exec Display Regex Logic Function Functions Target Layout View Output Control Execute Call Data Fetch Action Execution Check Properties Outputs Returns Output Method Object Execution Target Check Functions Match Array Execute Props Control Formats Map Properties Return Variable Handling Process Return Formats Layout Object Object Setup Variables Function Layout Arrays Formatting Props Maps Code Execution Return Action Run Properties Functions Arrays Mapping Rendering Outputs Value Returns Pattern Variables Outputs Scope String Components Prop
      const graphResponse = await getGraphData(graphId)
      
      if (graphResponse.success && graphResponse.data) {
        const newData = graphResponse.data
        const newNodeCount = newData.node_count || newData.nodes?.length || 0
        const oldNodeCount = graphData.value?.node_count || graphData.value?.nodes?.length || 0
        
        // DEBUG: Graph data fetched
        
        // If Array diff do Trigger DOM / D3 Update View
        if (newNodeCount !== oldNodeCount || !graphData.value) {
          graphData.value = newData
          await nextTick()
          renderGraph()
        }
      }
    }
  } catch (err) {
    // DEBUG: Graph data fetch
  }
}

// Backend Background Loops Data Update Visual UI Progress Sync Check Task Status Rest GET Request Response Set Intervals Timeout Controls Function Handlers Event Loops JS Wait
const startPollingTask = (taskId) => {
  // Run Fast API Poll Exec One Time
  pollTaskStatus(taskId)
  
  // E então polled...
  pollTimer = setInterval(() => {
    pollTaskStatus(taskId)
  }, 2000)
}

// Results Run Run Fetch Action Maps Fetch Methods Display Target Call Array Response Array Value Process Regex Target Variable Output Output Results Format Display Regex Exec Function Target Check Result Setup Displays Code Process Execute Returns Methods Map Scope Mapping Execution Logic Display Method Target Response Setup Logic App Returns Action Scope Run Outputs Component Action Execution Return Map Setup Formats Output Returns Call Rendering Display Scope Component Data Arrays Fetch View Control Execution Method Methods Return Arrays Value Variables Object Event Displays Returns String Fetch Layout Methods Action Result Map Output Result Results Action Render
const pollTaskStatus = async (taskId) => {
  try {
    const response = await getTaskStatus(taskId)
    
    if (response.success) {
      const task = response.data
      
      // Reflected View Progress Updates Var To Template DOM Watch.
      buildProgress.value = {
        progress: task.progress || 0,
        message: task.message || 'Processando...'
      }
      
      // DEBUG: Task status
      
      if (task.status === 'completed') {
        // DEBUG: Graph build success
        
        stopPolling()
        stopGraphPolling()
        currentPhase.value = 2
        
        // Sync Status Number Logic Display Check Vars Finished Ends State OK Success Vue Reactive Models View Template Update Process Bar Finish To Start Values Setup Final Limits Call Methods State Changes Reactivity Systems Update Hooks Fire Methods After Change Value Events Emits Result Values Number Boolean Flags
        buildProgress.value = {
          progress: 100,
          message: 'Concluído，Loading Graph Viewer Display Result Mapping Setup Value Formatting Map Logic Rendering Code Formats Prop Handling Outputs Results Outputs Target Result Maps Variables Execute Target String Event Output Map Execution Output Results Prop Mapping Action Returns Action Methods Object Arrays Results Action Methods Check String Mapping Component Output Layout Fetch Handle Properties Logic Display View Map Action Return Arrays Method...'
        }
        
        // Reload Force Override Project API Call graph_id
        const projectResponse = await getProject(currentProjectId.value)
        if (projectResponse.success) {
          projectData.value = projectResponse.data
          
          // Final Data Merge Display Visual Vectors Render From Source JSON DB Object Tree Graph
          if (projectResponse.data.graph_id) {
            // DEBUG: Loading full relational base
            await loadGraph(projectResponse.data.graph_id)
            // DEBUG: Nodes and edges rendered
          }
        }
        
        // Var Progress Resets Value 0 Number
        buildProgress.value = null
      } else if (task.status === 'failed') {
        stopPolling()
        stopGraphPolling()
        error.value = 'Construir GrafoError Catch Target Map Array Formatting Flow Maps Action Check Displays Displays Setup Values Values Flow Output Response Return Methods Regex Variable Setup Execute Component String Map Logic Mapping Outputs String Output: ' + (task.error || 'Desconhecimento API ERROR...')
        buildProgress.value = null
      }
    }
  } catch (err) {
    // DEBUG: Poll task error
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Load Fetch Graph From REST GraphId.
const loadGraph = async (graphId) => {
  try {
    graphLoading.value = true
    const response = await getGraphData(graphId)
    
    if (response.success) {
      graphData.value = response.data
      await nextTick()
      renderGraph()
    }
  } catch (err) {
    // DEBUG: Load graph error
  } finally {
    graphLoading.value = false
  }
}

// Render Flow Graphics View Node & Links... (D3.js)
const renderGraph = () => {
  if (!graphSvg.value || !graphData.value) {
    // DEBUG: Cannot render - missing svg/data
    return
  }
  
  const container = graphContainer.value
  if (!container) {
    // DEBUG: Cannot render - missing container
    return
  }
  
  // Bounds Dom Elements Base
  const rect = container.getBoundingClientRect()
  const width = rect.width || 800
  const height = (rect.height || 600) - 60
  
  if (width <= 0 || height <= 0) {
    // DEBUG: Cannot render - invalid dimensions
    return
  }
  
  // DEBUG: Rendering graph
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
  
  svg.selectAll('*').remove()
  
  // 处理nósLogs JSON
  const nodesData = graphData.value.nodes || []
  const edgesData = graphData.value.edges || []
  
  if (nodesData.length === 0) {
    // DEBUG: No nodes to render
    // Vazio / Clear State
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', '#999')
      .text('Fetching... Aguardando DB....')
    return
  }
  
  // Nova InstâncianósMap Reference Names Labels
  const nodeMap = {}
  nodesData.forEach(n => {
    nodeMap[n.uuid] = n
  })
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || 'Documento Anonimo Base Sem Título',
    type: n.labels?.find(l => l !== 'Entity' && l !== 'Node') || 'Entity',
    rawData: n // RAW Save State
  }))
  
  // Nova InstâncianósIDClean Null Edges Render Setup App Component Props Function Fetch App Props Fetch Code Response Object Arrays Returns Code Variable Result Call Action Variables Exec Mapping Regex Fetch Returns Setup Displays Regex Check Displays Output Props Map Match Scope Control Component Action Layout Displays Setup Event Outputs Mapping Returns Action Logic Handling
  const nodeIds = new Set(nodes.map(n => n.id))
  
  const edges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED_TO',
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name || 'Identificador Unknown?',
        target_name: nodeMap[e.target_node_uuid]?.name || 'Identificador Unknown?'
      }
    }))
  
  // DEBUG: Node and edge count
  
  // Color Palletes Node Array Map Hexes
  const types = [...new Set(nodes.map(n => n.type))]
  const colorScale = d3.scaleOrdinal()
    .domain(types)
    .range(['#FF6B35', '#004E89', '#7B2D8E', '#1A936F', '#C5283D', '#E9724C', '#2D3436', '#6C5CE7'])
  
  // D3 Force Graph Logic Apply Setup Constraints Simulation Links Force Center Adjust Multiplier Scales Nodes Base Models Array Variables Visual
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))
  
  // Pan & Zoom
  const g = svg.append('g')
  
  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))
  
  // D3 Stroke Lines Clickable Transparent Large Hitboxes Paths Render Generator SVG Appends Enter Updates Call）
  const linkGroup = g.append('g')
    .attr('class', 'links')
    .selectAll('g')
    .data(edges)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })
  
  // Edges Thin Strokes Styles D3
  const link = linkGroup.append('line')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6)
  
  // Transparent Broad Strokes Interactor Select Links Mouse Events.
  linkGroup.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)
  
  // Selos Racionais da Aresta
  const linkLabel = g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', '#999')
    .attr('text-anchor', 'middle')
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)
  
  // Renderizar D3 Context Handling Flow Response Method Execute Layout Code Formats Layout Setup Control Formatting Event Scope Displays Methods Event Handling String Maps Return Flow Maps View Call Outputs Check Output Result Checknós
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, colorScale(d.type))
    })
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
  
  node.append('circle')
    .attr('r', 10)
    .attr('fill', d => colorScale(d.type))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('class', 'node-circle')
  
  node.append('text')
    .attr('dx', 14)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')
  
  // 点击空白处Botão de Ocultar Visor de Dados Box
  svg.on('click', () => {
    closeDetailPanel()
  })
  
  simulation.on('tick', () => {
    // Refresh Bounds Dom Links Path Events Positions ReRender Arrays Map For Links Values Positions）
    linkGroup.selectAll('line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    
    // Tick Positions D3 Render Links text.
    linkLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 5)
    
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }
  
  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }
  
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

// Watch Var Data Changes.
watch(graphData, () => {
  if (graphData.value) {
    nextTick(() => renderGraph())
  }
})

// Lifecycle Vue Hooks.
onMounted(() => {
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
})
</script>

<style scoped>
/* Vars Data */
:root {
  --color-on-background: var(--color-on-background);
  --color-surface: var(--color-surface);
  --gray-light: var(--color-surface-container-low);
  --gray-border: var(--color-outline);
  --gray-text: var(--color-muted);
}

.process-page {
  min-height: 100vh;
  background: var(--color-surface);
  font-family: 'JetBrains Mono', 'Noto Sans SC', monospace;
  overflow: hidden; /* Prevent body scroll in fullscreen */
}

/* Navegação */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--color-on-background);
  color: var(--color-surface);
  z-index: 10;
  position: relative;
}

.nav-brand {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.step-badge {
  background: var(--color-error);
  color: var(--color-surface);
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: 2px;
}

.step-name {
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: var(--color-surface);
}

.nav-status {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-muted);
  margin-right: 8px;
}

.status-dot.processing {
  background: var(--color-error);
  animation: pulse 1.5s infinite;
}

.status-dot.completed {
  background: var(--color-success);
}

.status-dot.error {
  background: var(--color-error);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.75rem;
  color: var(--color-disabled);
}

/* Matriz Central Viewer. */
.main-content {
  display: flex;
  height: calc(100vh - 56px);
  position: relative;
}

/* Observatório esquerdo - 50% default */
.left-panel {
  width: 50%;
  flex: none; /* Fixed width initially */
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-outline);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--color-surface);
  z-index: 5;
}

.left-panel.full-screen {
  width: 100%;
  border-right: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface);
  height: 50px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco {
  color: var(--color-error);
  font-size: 0.8rem;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.75rem;
  color: var(--color-muted);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-val {
  font-weight: 600;
  color: var(--color-on-surface);
}

.stat-divider {
  color: var(--color-outline);
}

.action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-muted);
  border-radius: 0px;
  font-family: var(--font-machine);
  font-weight: 600;
}

.action-btn:hover:not(:disabled) {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.icon-refresh, .icon-fullscreen {
  font-size: 1rem;
  line-height: 1;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Canvas Box Grafos. */
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-loading,
.graph-waiting,
.graph-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.loading-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.loading-ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 1.5s linear infinite;
}

.loading-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  border-top-color: #000;
}

.loading-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-right-color: var(--color-error);
  animation-delay: 0.2s;
}

.loading-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  border-bottom-color: var(--color-muted);
  animation-delay: 0.4s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-text,
.waiting-text {
  font-size: 0.9rem;
  color: var(--color-on-surface);
  margin: 0 0 8px;
}

.waiting-hint {
  font-size: 0.8rem;
  color: var(--color-disabled);
  margin: 0;
}

.waiting-icon {
  margin-bottom: 20px;
}

.network-icon {
  width: 100px;
  height: 100px;
  opacity: 0.6;
}

.graph-view {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-building-hint {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 107, 53, 0.1);
  border: 1px solid var(--color-error);
  font-size: 0.8rem;
  color: var(--color-error);
}

.building-dot {
  width: 8px;
  height: 8px;
  background: var(--color-error);
  border-radius: 50%;
  animation: pulse 1s infinite;
}

/* nós/Edge Descriptor Output Setup Fetch Check Props Fetch Format Array Regex Displays Logic Process Regex Layout Model Rendering State Setup Event Outputs Code Map Outputs Value Code Outputs Output String Logic Run ExecutePanel Console Area Box */
.detail-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 320px;
  max-height: calc(100% - 32px);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.detail-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-surface-container-low);
  border-bottom: 1px solid var(--color-outline);
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-on-surface);
}

.detail-badge {
  padding: 2px 10px;
  font-size: 0.75rem;
  color: var(--color-surface);
  border-radius: 2px;
}

.detail-close {
  margin-left: auto;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: var(--color-disabled);
  cursor: pointer;
  transition: color 0.2s;
}

.detail-close:hover {
  color: var(--color-on-surface);
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--color-disabled);
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 0.85rem;
  color: var(--color-on-surface);
  word-break: break-word;
}

.detail-value.uuid {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: var(--color-muted);
}

.detail-section {
  margin-bottom: 12px;
}

.detail-summary {
  margin: 8px 0 0 0;
  font-size: 0.85rem;
  color: var(--color-on-surface);
  line-height: 1.6;
  padding: 10px;
  background: var(--color-background);
  border-left: 3px solid var(--color-error);
}

.detail-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  color: var(--color-muted);
}

/* Edge Descriptor Output Setup Fetch Check Props Fetch Format Array Regex Displays Logic Process Regex Layout Model Rendering State Setup Event Outputs Code Map Outputs Value Code Outputs Output String Logic Run ExecuterelaçõesRender View Template */
.edge-relation {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-background);
  border: 1px solid var(--color-outline);
}

.edge-source,
.edge-target {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-on-surface);
}

.edge-arrow {
  color: var(--color-disabled);
}

.edge-type {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-error);
  color: var(--color-surface);
}

.detail-value.highlight {
  font-weight: 600;
  color: var(--color-on-background);
}

.detail-subtitle {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-on-surface);
  margin: 16px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-outline);
}

/* Properties JSON Params Box View Dict Iterate UI Panel Div Render Data Lists Props */
.properties-list {
  margin-top: 8px;
  padding: 10px;
  background: var(--color-background);
  border: 1px solid var(--color-outline);
}

.property-item {
  display: flex;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.property-item:last-child {
  margin-bottom: 0;
}

.property-key {
  color: var(--color-muted);
  margin-right: 8px;
  font-family: 'JetBrains Mono', monospace;
}

.property-value {
  color: var(--color-on-surface);
  word-break: break-word;
}

/* Episodes Listas Arrays */
.episodes-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: block;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  color: var(--color-muted);
  word-break: break-all;
}

.error-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 10px;
}

/* Legend. Nodes Classific. */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid var(--color-outline);
  background: var(--color-surface-container-low);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  color: var(--color-on-surface);
}

.legend-count {
  color: var(--color-disabled);
}

/* Aresta Observadora Direita - 50% default */
.right-panel {
  width: 50%;
  flex: none;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  opacity: 1;
}

.right-panel.hidden {
  width: 0;
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.right-panel .panel-header.dark-header {
  background: var(--color-on-background);
  color: var(--color-surface);
  border-bottom: none;
}

.right-panel .header-icon {
  color: var(--color-error);
  margin-right: 8px;
}

/* Steps List Item List Panel Info Structs UI: */
.process-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Stage Process State Rendering Execution Output Exec Output Formats Methods Action Props Code Maps Run Flow Exec Handle Mapping Returns Prop Format Handling Fetch Flow Setup Flow Returns Mapping Display Arrays Layout Setup Variables Action Mapping Layout Output Functions Display Flow Call Display Match Arrays Response Handling FormatFase */
.process-phase {
  margin-bottom: 24px;
  border: 1px solid var(--color-outline);
  opacity: 0.5;
  transition: all 0.3s;
}

.process-phase.active,
.process-phase.completed {
  opacity: 1;
}

.process-phase.active {
  border-color: #FF6B35;
}

.process-phase.completed {
  border-color: var(--color-success);
}

.phase-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: var(--color-surface-container-low);
  border-bottom: 1px solid var(--color-outline);
}

.process-phase.active .phase-header {
  background: var(--color-error-bg);
}

.process-phase.completed .phase-header {
  background: var(--color-success-bg);
}

.phase-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-outline);
  line-height: 1;
}

.process-phase.active .phase-num {
  color: var(--color-error);
}

.process-phase.completed .phase-num {
  color: var(--color-success);
}

.phase-info {
  flex: 1;
}

.phase-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.phase-api {
  font-size: 0.75rem;
  color: var(--color-disabled);
  font-family: 'JetBrains Mono', monospace;
}

.phase-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--color-outline);
  color: var(--color-muted);
}

.phase-status.active {
  background: var(--color-error);
  color: var(--color-surface);
}

.phase-status.completed {
  background: var(--color-success);
  color: var(--color-surface);
}

/* FaseDescritivo Total */
.phase-detail {
  padding: 16px;
}

/* Entidades Rótulo Base. */
.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  color: var(--color-on-surface);
}

/* relaçõesListas Arrays */
.relation-list {
  font-size: 0.8rem;
}

.relation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--color-outline);
}

.relation-item:last-child {
  border-bottom: none;
}

.rel-source,
.rel-target {
  color: var(--color-on-surface);
}

.rel-arrow {
  color: var(--color-outline);
}

.rel-name {
  color: var(--color-error);
  font-weight: 500;
}

.relation-more {
  padding-top: 8px;
  color: var(--color-disabled);
  font-size: 0.75rem;
}

/* Gerar OntologiaAndamento % */
.ontology-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-bg);
}

.progress-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-error-bg);
  border-top-color: #FF6B35;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.progress-text {
  font-size: 0.85rem;
  color: var(--color-on-surface);
}

/* Queue Delay Status DB Check Vars Loops Value */
.waiting-state {
  padding: 16px;
  background: var(--color-background);
  border: 1px dashed var(--color-outline);
  text-align: center;
}

.waiting-hint {
  font-size: 0.85rem;
  color: var(--color-disabled);
}

/* ProgressBar HTML */
.progress-bar {
  height: 6px;
  background: var(--color-surface-container-highest, var(--color-outline));
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--profile-primary, var(--color-error));
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.progress-message {
  color: var(--color-muted);
}

.progress-percent {
  color: var(--color-error);
  font-weight: 600;
}

/* Resultados */
.build-result {
  display: flex;
  gap: 16px;
}

.result-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: var(--color-surface-container-low);
}

.result-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-on-background);
  margin-bottom: 4px;
}

.result-label {
  font-size: 0.7rem;
  color: var(--color-disabled);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Avançar Botão Box */
.next-step-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-outline);
}

.next-step-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: var(--color-on-background);
  color: var(--color-surface-container-highest);
  border: none;
  font-size: 1rem;
  font-family: var(--font-machine);
  font-weight: 600;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 0px;
}

.next-step-btn:hover:not(:disabled) {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.next-step-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-arrow {
  font-size: 1.2rem;
}

/* ProjetoPanel Console Area Box */
.project-panel {
  border-top: 1px solid var(--color-outline);
  background: var(--color-surface-container-low);
}

.project-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-outline);
}

.project-icon {
  color: var(--color-error);
}

.project-title {
  font-size: 0.85rem;
  font-weight: 600;
}

.project-details {
  padding: 16px 24px;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-outline);
  font-size: 0.8rem;
}

.project-item:last-child {
  border-bottom: none;
}

.item-label {
  color: var(--color-disabled);
  flex-shrink: 0;
}

.item-value {
  color: var(--color-on-surface);
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

.item-value.code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: var(--color-muted);
}

/* 响应式 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100% !important;
    border-right: none;
    border-bottom: 1px solid var(--color-outline);
    height: 50vh;
  }
  
  .right-panel {
    width: 100% !important;
    height: 50vh;
    opacity: 1 !important;
    transform: none !important;
  }
  
  .right-panel.hidden {
      display: none;
  }
}
</style>
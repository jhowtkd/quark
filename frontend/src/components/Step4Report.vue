<template>
  <div class="report-panel">
    <!-- Main Split Layout -->
    <div class="main-split-layout">
      <!-- LEFT PANEL: Report Style -->
      <div class="left-panel report-style" ref="leftPanel">
        <div v-if="reportOutline" class="report-content-wrapper">
          <!-- Report Header -->
          <div class="report-header-block">
            <div class="report-meta">
              <span class="report-tag">Prediction Report</span>
              <span class="report-id">ID: {{ reportId || 'REF-2024-X92' }}</span>
            </div>
            <h1 class="main-title">{{ reportOutline.title }}</h1>
            <p class="sub-title">{{ reportOutline.summary }}</p>
            <div class="header-divider"></div>
          </div>

          <!-- Sections List -->
          <div class="sections-list">
            <div 
              v-for="(section, idx) in reportOutline.sections" 
              :key="idx"
              class="report-section-item"
              :class="{ 
                'is-active': currentSectionIndex === idx + 1,
                'is-completed': isSectionCompleted(idx + 1),
                'is-pending': !isSectionCompleted(idx + 1) && currentSectionIndex !== idx + 1,
                'dd-tese': isDueDiligenceSection(section.title, 'tese'),
                'dd-evidencias': isDueDiligenceSection(section.title, 'evidencias'),
                'dd-fragilidades': isDueDiligenceSection(section.title, 'fragilidades'),
                'dd-premissas': isDueDiligenceSection(section.title, 'premissas'),
                'dd-cenarios': isDueDiligenceSection(section.title, 'cenarios')
              }"
            >
              <div class="section-header-row" @click="toggleSectionCollapse(idx)" :class="{ 'clickable': isSectionCompleted(idx + 1) }">
                <span class="section-number">{{ String(idx + 1).padStart(2, '0') }}</span>
                <h3 class="section-title">{{ section.title }}</h3>
                <span v-if="getDDSectionLabel(section.title)" class="dd-badge">{{ getDDSectionLabel(section.title) }}</span>
                <svg 
                  v-if="isSectionCompleted(idx + 1)" 
                  class="collapse-icon" 
                  :class="{ 'is-collapsed': collapsedSections.has(idx) }"
                  viewBox="0 0 24 24" 
                  width="20" 
                  height="20" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2"
                >
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
              
              <div class="section-body" v-show="!collapsedSections.has(idx)">
                <!-- Completed Content -->
                <div v-if="generatedSections[idx + 1]" class="generated-content" v-html="renderSafeSectionContent(idx + 1)"></div>
                
                <!-- Contamination Warning Fallback -->
                <div v-else-if="contaminatedSections.has(idx + 1)" class="contamination-warning">
                  <div class="warning-icon">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                      <line x1="12" y1="9" x2="12" y2="13"></line>
                      <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                  </div>
                  <span class="warning-text">{{ $t('contamination.contentRemoved') }}</span>
                </div>
                
                <!-- Loading State -->
                <div v-else-if="currentSectionIndex === idx + 1" class="loading-state">
                  <div class="loading-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" stroke-width="4" stroke="#E5E7EB"></circle>
                      <path d="M12 2a10 10 0 0 1 10 10" stroke-width="4" stroke="#4B5563" stroke-linecap="round"></path>
                    </svg>
                  </div>
                  <span class="loading-text">{{ $t('step4.generatingSection', { title: section.title }) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Waiting State -->
        <div v-if="!reportOutline" class="waiting-placeholder">
          <div class="waiting-animation">
            <div class="waiting-ring"></div>
            <div class="waiting-ring"></div>
            <div class="waiting-ring"></div>
          </div>
          <span class="waiting-text">{{ $t('step4.waitingForReportAgent') }}</span>
        </div>
      </div>

      <!-- RIGHT PANEL: Workflow Timeline -->
      <div class="right-panel" ref="rightPanel">
        <div class="panel-header" :class="`panel-header--${activeStep.status}`" v-if="!isComplete">
          <span class="header-dot" v-if="activeStep.status === 'active'"></span>
          <span class="header-index mono">{{ activeStep.noLabel }}</span>
          <span class="header-title">{{ activeStep.title }}</span>
          <span class="header-meta mono" v-if="activeStep.meta">{{ activeStep.meta }}</span>
        </div>

        <!-- Workflow Overview (flat, status-based palette) -->
        <div class="workflow-overview" v-if="agentLogs.length > 0 || reportOutline">
          <div class="workflow-metrics">
            <div class="metric">
              <span class="metric-label">Sections</span>
              <span class="metric-value mono">{{ completedSections }}/{{ totalSections }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Elapsed</span>
              <span class="metric-value mono">{{ formatElapsedTime }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Tools</span>
              <span class="metric-value mono">{{ totalToolCalls }}</span>
            </div>
            <div class="metric metric-right">
              <span class="metric-pill" :class="`pill--${statusClass}`">{{ statusText }}</span>
            </div>
          </div>

          <div class="workflow-steps" v-if="workflowSteps.length > 0">
            <div
              v-for="(step, sidx) in workflowSteps"
              :key="step.key"
              class="wf-step"
              :class="`wf-step--${step.status}`"
            >
              <div class="wf-step-connector">
                <div class="wf-step-dot"></div>
                <div class="wf-step-line" v-if="sidx < workflowSteps.length - 1"></div>
              </div>

              <div class="wf-step-content">
                <div class="wf-step-title-row">
                  <span class="wf-step-index mono">{{ step.noLabel }}</span>
                  <span class="wf-step-title">{{ step.title }}</span>
                  <span class="wf-step-meta mono" v-if="step.meta">{{ step.meta }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Next Step Button - Function Loop Scope Action App Logic Component Format Variables Objects Event Exec String Exec Call Action Mapping Process Handling State Layout Variables Logic Setup App Value String Event Formats Scope Rendering Execute Array View Outputs Maps Exec Displays Display Map Event App Scope Output Process Variables Return Call Return Array Outputs Outputs Run Method Output Objects Event Outputs Execute Logic Execute App Output Execution Prop Handle Return Setup Execution Result Target Regex Execute Components Methods Flow Layout Prop Exec Map Components Target Method Displays Arrays Logic Method Displays Array Format Execution Data Call Mapping Process Exec Process Event Results Formats Flow -->
          <button v-if="isComplete" class="next-step-btn" @click="goToInteraction">
            <span>{{ $t('step4.goToInteraction') }}</span>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>

          <div class="workflow-divider"></div>
        </div>

        <div class="workflow-timeline">
          <TransitionGroup name="timeline-item">
            <div 
              v-for="(log, idx) in displayLogs" 
              :key="log.timestamp + '-' + idx"
              class="timeline-item"
              :class="getTimelineItemClass(log, idx, displayLogs.length)"
            >
              <!-- Timeline Connector -->
              <div class="timeline-connector">
                <div class="connector-dot" :class="getConnectorClass(log, idx, displayLogs.length)"></div>
                <div class="connector-line" v-if="idx < displayLogs.length - 1"></div>
              </div>
              
              <!-- Timeline Content -->
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="action-label">{{ getActionLabel(log.action) }}</span>
                  <span class="action-time">{{ formatTime(log.timestamp) }}</span>
                </div>
                
                <!-- Action Body - Different for each type -->
                <div class="timeline-body" :class="{ 'collapsed': isLogCollapsed(log) }" @click="toggleLogExpand(log)">
                  
                  <!-- Report Start -->
                  <template v-if="log.action === 'report_start'">
                    <div class="info-row">
                      <span class="info-key">Simulation</span>
                      <span class="info-val mono">{{ log.details?.simulation_id }}</span>
                    </div>
                    <div class="info-row" v-if="log.details?.simulation_requirement">
                      <span class="info-key">Requirement</span>
                      <span class="info-val">{{ log.details.simulation_requirement }}</span>
                    </div>
                  </template>

                  <!-- Planning -->
                  <template v-if="log.action === 'planning_start'">
                    <div class="status-message planning">{{ log.details?.message }}</div>
                  </template>
                  <template v-if="log.action === 'planning_complete'">
                    <div class="status-message success">{{ log.details?.message }}</div>
                    <div class="outline-badge" v-if="log.details?.outline">
                      {{ log.details.outline.sections?.length || 0 }} sections planned
                    </div>
                  </template>

                  <!-- Section Start -->
                  <template v-if="log.action === 'section_start'">
                    <div class="section-tag">
                      <span class="tag-num">#{{ log.section_index }}</span>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>
                  
                  <!-- Section Content Generated (Parcial done bg works left) -->
                  <template v-if="log.action === 'section_content'">
                    <div class="section-tag content-ready">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                      </svg>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>

                  <!-- Section Complete (State Updates View Render Variables Formats Maps Target Handling Mapping Value Returns Function Properties Component Prop Call Results Methods Action Displays Object Event Components Array Props Setup Displays Objects Returns Logic Fetch Run Loop Flow Values Mapping Returns Results Mapping Function Flow Logic Action Event Component Map State Results Response Mapping Scope Loop Object Handling State Map Display Rendering Scope Data Objects Layout Execution Execute Formatting Components Layout Execute Render View Component Values Output Return Rendering Outputs Results Execution Output Props Execute Function Setup Loop Map Methods Displays Fetch Event Object Props Maps Arrays Data Flow Action Values Target Returns Event Displays Logic Regex Handling Return Layout Handling Props Pattern View Action Data State Handling Loop Handling Action Displays Mapping Control Returns Mapping Mapping Control Logic Values View Exec Arrays Execution Formatting Method Values State Output Component Handling Map Function Components Mapping Components Properties Output Prop Flow Object Setup Mapping Map Array Output Functions Response Method Display Data Mapping Variables Control Arrays Flow Array Execution Variables Component Loop Array Method Logic Methods) -->
                  <template v-if="log.action === 'section_complete'">
                    <div class="section-tag completed">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>

                  <!-- Tool Call -->
                  <template v-if="log.action === 'tool_call'">
                    <div class="tool-badge" :class="'tool-' + getToolColor(log.details?.tool_name)">
                      <!-- Deep Insight - Lightbulb -->
                      <svg v-if="getToolIcon(log.details?.tool_name) === 'lightbulb'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.5V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.5A7 7 0 0 0 12 2z"></path>
                      </svg>
                      <!-- Panorama Search - Globe -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'globe'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                      </svg>
                      <!-- Agent Interview - Users -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'users'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                      </svg>
                      <!-- Quick Search - Zap -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'zap'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                      </svg>
                      <!-- Graph Stats - Chart -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'chart'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                      </svg>
                      <!-- Entity Query - Database -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'database'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                      </svg>
                      <!-- Default - Tool -->
                      <svg v-else class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
                      </svg>
                      {{ getToolDisplayName(log.details?.tool_name) }}
                    </div>
                    <div v-if="log.details?.parameters && expandedLogs.has(log.timestamp)" class="tool-params">
                      <pre>{{ formatParams(log.details.parameters) }}</pre>
                    </div>
                  </template>

                  <!-- Tool Result -->
                  <template v-if="log.action === 'tool_result'">
                    <div class="result-wrapper" :class="'result-' + log.details?.tool_name">
                      <!-- Hide result-meta for tools that show stats in their own header -->
                      <div v-if="!['interview_agents', 'insight_forge', 'panorama_search', 'quick_search'].includes(log.details?.tool_name)" class="result-meta">
                        <span class="result-tool">{{ getToolDisplayName(log.details?.tool_name) }}</span>
                        <span class="result-size">{{ formatResultSize(log.details?.result_length) }}</span>
                      </div>
                      
                      <!-- Structured Result Display -->
                      <div v-if="!showRawResult[log.timestamp]" class="result-structured">
                        <!-- Interview Agents - Special Display -->
                        <template v-if="log.details?.tool_name === 'interview_agents'">
                          <InterviewDisplay :result="parseInterview(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Insight Forge -->
                        <template v-else-if="log.details?.tool_name === 'insight_forge'">
                          <InsightDisplay :result="parseInsightForge(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Panorama Search -->
                        <template v-else-if="log.details?.tool_name === 'panorama_search'">
                          <PanoramaDisplay :result="parsePanorama(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Quick Search -->
                        <template v-else-if="log.details?.tool_name === 'quick_search'">
                          <QuickSearchDisplay :result="parseQuickSearch(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Default -->
                        <template v-else>
                          <pre class="raw-preview">{{ truncateText(log.details?.result, 300) }}</pre>
                        </template>
                      </div>
                      
                      <!-- Raw Result -->
                      <div v-else class="result-raw">
                        <pre>{{ log.details?.result }}</pre>
                      </div>
                    </div>
                  </template>

                  <!-- LLM Response -->
                  <template v-if="log.action === 'llm_response'">
                    <div class="llm-meta">
                      <span class="meta-tag">Iteration {{ log.details?.iteration }}</span>
                      <span class="meta-tag" :class="{ active: log.details?.has_tool_calls }">
                        Tools: {{ log.details?.has_tool_calls ? 'Yes' : 'No' }}
                      </span>
                      <span class="meta-tag" :class="{ active: log.details?.has_final_answer, 'final-answer': log.details?.has_final_answer }">
                        Final: {{ log.details?.has_final_answer ? 'Yes' : 'No' }}
                      </span>
                    </div>
                    <!-- Alert Box On Final Outputs -->
                    <div v-if="log.details?.has_final_answer" class="final-answer-hint">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      <span>{{ $t('step4.sectionContentGenerated', { title: log.section_title }) }}</span>
                    </div>
                    <div v-if="expandedLogs.has(log.timestamp) && log.details?.response" class="llm-content">
                      <pre>{{ log.details.response }}</pre>
                    </div>
                  </template>

                  <!-- Report Complete -->
                  <template v-if="log.action === 'report_complete'">
                    <div class="complete-banner">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                      </svg>
                      <span>{{ $t('step4.reportGenerationComplete') }}</span>
                    </div>
                  </template>
                </div>

                <!-- Footer: Elapsed Time + Action Buttons -->
                <div class="timeline-footer" v-if="log.elapsed_seconds || (log.action === 'tool_call' && log.details?.parameters) || log.action === 'tool_result' || (log.action === 'llm_response' && log.details?.response)">
                  <span v-if="log.elapsed_seconds" class="elapsed-badge">+{{ log.elapsed_seconds.toFixed(1) }}s</span>
                  <span v-else class="elapsed-placeholder"></span>
                  
                  <div class="footer-actions">
                    <!-- Tool Call: Show/Hide Params -->
                    <button v-if="log.action === 'tool_call' && log.details?.parameters" class="action-btn" @click.stop="toggleLogExpand(log)">
                      {{ expandedLogs.has(log.timestamp) ? 'Hide Params' : 'Show Params' }}
                    </button>
                    
                    <!-- Tool Result: Raw/Structured View -->
                    <button v-if="log.action === 'tool_result'" class="action-btn" @click.stop="toggleRawResult(log.timestamp, $event)">
                      {{ showRawResult[log.timestamp] ? 'Structured View' : 'Raw Output' }}
                    </button>
                    
                    <!-- LLM Response: Show/Hide Response -->
                    <button v-if="log.action === 'llm_response' && log.details?.response" class="action-btn" @click.stop="toggleLogExpand(log)">
                      {{ expandedLogs.has(log.timestamp) ? 'Hide Response' : 'Show Response' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <!-- Empty State -->
          <div v-if="agentLogs.length === 0 && !isComplete" class="workflow-empty">
            <div class="empty-pulse"></div>
            <span>{{ $t('step4.waitingForAgentActivity') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Console Logs -->
    <div class="console-logs">
      <div class="log-header">
        <span class="log-title">{{ $t('step4.consoleOutput') }}</span>
        <span class="log-id">{{ reportId || $t('step4.noReport') }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in consoleLogs" :key="idx">
          <span class="log-msg" :class="getLogLevelClass(log)">{{ log }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick, h, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getAgentLog, getConsoleLog } from '../api/report'
import { detectContamination, sanitizeContent, validateAgentLog } from '../utils/payloadValidator'

const router = useRouter()
const { t } = useI18n()

const props = defineProps({
  reportId: String,
  simulationId: String,
  systemLogs: Array
})

const emit = defineEmits(['add-log', 'update-status'])

// Navigation
const goToInteraction = () => {
  if (props.reportId) {
    router.push({ name: 'Interaction', params: { reportId: props.reportId } })
  }
}

// State
const agentLogs = ref([])
const consoleLogs = ref([])
const agentLogLine = ref(0)
const consoleLogLine = ref(0)
const reportOutline = ref(null)
const currentSectionIndex = ref(null)
const generatedSections = ref({})
const expandedContent = ref(new Set())
const expandedLogs = ref(new Set())
const collapsedSections = ref(new Set())
const isComplete = ref(false)
const startTime = ref(null)
const leftPanel = ref(null)
const rightPanel = ref(null)
const logContent = ref(null)
const showRawResult = reactive({})

// Contamination tracking state
const contaminatedSections = ref(new Set()) // Set of section indices that are contaminated
const sectionWarnings = reactive({}) // { [sectionIndex]: { reason: string, severity: string } }

// Toggle functions
const toggleRawResult = (timestamp, event) => {
  // Salvar Params.Maps Logic Functions Handle Event Handling Components Output Values Component Logic Execute Displays Event Return Scope Handle Display Process Fetch Rendering Handling Display Handling Execution Results Array Maps Event Methods Event Return Map Logic Output Objects Method Methods Return Fetch Response Arrays Handling Check Return Call Format Layout Response Mapping Fetch Logic Formats Arrays Control Check Objects Results String Formats Handling Return Arrays Method Array Setup Object Variables Formatting Run Call Check Flow Method Flow Handling Setup Pattern Setup Component Setup App Displays Event Arrays Results Values Data Logic Logic Flow Properties Match Results Result State Run Event Flow View Arrays Data Result Map Fetch Mapping Target Result Function Event Loop Target Array Scope Values Outputs Flow Action Methods Map Properties Arrays Methods Displays Objects Check Response Return Execution
  const button = event?.target
  const buttonRect = button?.getBoundingClientRect()
  const buttonTopBeforeToggle = buttonRect?.top
  
  // Virar State Vars
  showRawResult[timestamp] = !showRawResult[timestamp]
  
  // DOM NextTick Scroll Adjust Positions Sync Buttons View Ports Math
  if (button && buttonTopBeforeToggle !== undefined && rightPanel.value) {
    nextTick(() => {
      const newButtonRect = button.getBoundingClientRect()
      const buttonTopAfterToggle = newButtonRect.top
      const scrollDelta = buttonTopAfterToggle - buttonTopBeforeToggle
      
      // Components Setup Logic Check Model Layout Target Props Target Component Scope Outputs Flow Logic Event String Outputs Pattern Method Fetch Props Loop Rendering Flow Format Value Component Call Output Arrays Object Handling Variables Action Array Pattern Output Results Action Handling Result Result Results Execute Display Map Exec Setup Flow Logic String Handling Results Results Returns Displays Data Formatting Mapping Regex Method Outputs Function Components Layout Execute Components Return Displays View View Exec Output Results Execution Function Map Prop Execute Output Displays Arrays Code Call Event Data Variables Format Execute Flow Exec Output App Arrays Setup Code Component Prop Pattern Model View Rendering Flow Execute Results Result Call Array Flow Event Data Properties Variable Render Methods Loop Check Match Scope Scope Flow Outputs
      rightPanel.value.scrollTop += scrollDelta
    })
  }
}

const toggleSectionContent = (idx) => {
  if (!generatedSections.value[idx + 1]) return
  const newSet = new Set(expandedContent.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  expandedContent.value = newSet
}

const toggleSectionCollapse = (idx) => {
  // Fecha somente se concretizado
  if (!generatedSections.value[idx + 1]) return
  const newSet = new Set(collapsedSections.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  collapsedSections.value = newSet
}

const toggleLogExpand = (log) => {
  const newSet = new Set(expandedLogs.value)
  if (newSet.has(log.timestamp)) {
    newSet.delete(log.timestamp)
  } else {
    newSet.add(log.timestamp)
  }
  expandedLogs.value = newSet
}

const isLogCollapsed = (log) => {
  if (['tool_call', 'tool_result', 'llm_response'].includes(log.action)) {
    return !expandedLogs.value.has(log.timestamp)
  }
  return false
}

// Tool configurations with display names and colors
const toolConfig = {
  'insight_forge': {
    name: 'Deep Insight',
    color: 'purple',
    icon: 'lightbulb' // Light Map Methods Result Fetch Mapping Component Check Handling Formatting Scope Map Result Setup Returns Formatting Formats Array Methods Format Code Methods Components Rendering Display Execute Variables Action Setup Methods Components Outputs Displays Exec Method Handling Response Result Setup Method Outputs Execute Arrays Mapping Returns Props Object Logic Code Function Returns Call Action Output Display Results Variables Action Formatting Prop Value Regex Execute Scope Methods Target Return Component Displays Variables Scope Data Handling Layout Displays Execution Logic Display Object Properties Displays Arrays Map Object Component Props String Execution Setup Returns Map Objects Display Mapping Results Execute Property Setup Fetch Outputs Handling Variables Props Format Components State Response Format Prop Arrays Logic Array Result Map Displays Objects Format Functions Output Display Functions Arrays String Execution Execute - Insights Handling Component Props Format Handling Methods Rendering Display Data Target Layout Model Fetch Variables Map View Result Prop Components DOM Response Response Layout Result Fetch Method Render Model View Scope Result Flow Response Control Model Render Fetch Response Map Results Formatting Scope Variable Display Prop Process Handling Execution Return Values Layout Returns Rendering View Variables Formatting Return Setup Objects Format Returns Prop Variables Function Map Output Scope Call Action Handle Arrays Call Execute Props Methods Loop Object Exec Map Execute Logic DOM Flow Rendering Model Flow Rendering Response Values State DOM Prop Variable Data Fetch Run Run Formatting Flow Format Returns Method Displays Event Value Scope Rendering Map Map Map Returns Rendering
  },
  'panorama_search': {
    name: 'Panorama Search',
    color: 'blue',
    icon: 'globe' // Result Results Outputs Result Methods Execution Objects Mapping Setup Mapping Regex Handle Value Event Exec Execution Output Outputs Variables Fetch Objects Displays Action Maps Setup Variables Handle Handle Display Run Results Value Loop Action Layout Properties Object Component Response Formatting Prop Variables Action Flow Value Pattern Method Arrays Run Mapping Match Action Format Fetch Action Display Layout Displays State State Mapping Map Arrays Prop Call Component Event Method Values Action Map Execution Setup Map Mapping Handle Layout Layout Object Map Values Code - Panorama Seek Action Logic Maps Path Nodes Search BFS
  },
  'interview_agents': {
    name: 'Agent Interview',
    color: 'green',
    icon: 'users' // String Returns Methods Outputs Methods Displays Call Returns Pattern Loop Target View Arrays Values Variable Formatting Setup Returns Output Map State Map Mapping Handling Results Output Outputs Handling Regex Setup Object Object View Render Handle App Methods Methods Format Array Mapping Render Arrays Variables Component Output Code Arrays String App Exec Event Maps Flow Formats Output Returns Call Rendering Display Output Component Props Fetch Flow Display Object Display Call Action Format Flow Scope Execution Map Logic Execution Regex Code Event Method Target Exec Call Logic Flow Fetch Execute Component Call Scope Objects Render Results Fetch Return Display Action String Results - Value Pattern Array Regex Return Check Code Method Display Execution Displays Formatting Mapping Value Returns Render Output Outputs Map Model Format Properties Object Method Fetch Method App Formats Displays Action Array Function Render Map Setup Results Call Target Flow Objects Execute Arrays Format Outputs Regex Output Method Flow String Loop Variables Mapping Object String Object Setup Target Layout Formatting Code Properties Handling App Target Display Flow Results Call Variables Maps Data Execution Variables Response Flow Methods Scope Response View Layout Layout String Rendering Loop Flow Component Map Returns Handling Prop Component Response Props Mapping Execution Array Target Data Exec Call Action Object Call Display View Components Layout Displays Format Value Map Return Object State Variable Model Logic Output Output Exec Regex Displays Results Render Action Call Properties Flow Scope Handling Displays String Mapping Formats Return String State Components Variable Data Variables Prop Method Component Match Execute Logic Model Component Data Run Scope Response Map Flow Setup Function
  },
  'quick_search': {
    name: 'Quick Search',
    color: 'orange',
    icon: 'zap' // Values Call Rendering Target Loop Results Result Handling Exec View Variables Result Execution Components Variables Values Setup Properties Action Run Object Flow Flow Formats Functions Component Render Format Fetch Exec Displays Call Display Method Layout Action Response Flow Regex Handling Render Result Layout Setup Component Return Array Component Model Variable Fetch Run Response Loop Mapping Properties Flow Execution Method Methods Fetch Layout Exec String Code Flow Functions App Rendering View Scope Setup Variables Values Arrays Returns View Props Returns Regex Event Object Loop Rendering Display Call Displays Execute Data Check Exec Check Prop Run Match Displays Results Mapping Render Action View Arrays Logic Scope Prop Result Flow - Represents Quick Mode Action Event Type String Setup Mode Choice Variables Enum Const Target Function Setup Config Switch Code Control Check
  },
  'get_graph_statistics': {
    name: 'Graph Stats',
    color: 'cyan',
    icon: 'chart' // Result Functions Arrays Outputs Pattern Process Regex Map Setup String Returns Arrays Run Setup Run Array Object Setup Variables Execution Regex Map Execution Properties Target Call Maps Logic Displays Array Response Regex Process Handle Component View Execution Event Arrays Fetch String Maps Value Setup Format Component Methods Handling Regex Exec Flow Data Setup Match Response Display Loop Function Prop Props Logic Properties Method Outputs Prop Flow Action Map Results Render Regex Execution Props Format Code Model Return Variables Function Results Exec Return Execute Setup Properties Map Result Run Results Execution Displays Loop Action Event Prop Execute Target Event Regex Variable Methods Run Fetch Output Component Setup Action Run Return Output Execution Map State Result Data Formatting Model State Flow Fetch Map Method Components Flow Result Components Action Exec Action Match Execution Action Code Model Layout Match Response Model String Object Returns Match Returns Handling Values Exec Model Returns Displays Method Flow Array Control Render Flow Format Props Objects Loop String - Mapping Map Pattern Methods Map Formats Formatting Arrays Logic Results Handle Execution Run Results State Code Result Run Model Target Action Logic Event Loop Variables Components Run Model Output Return Component Arrays Render Arrays Value Formatting Call Handling Component Results Displays Value Mapping Formats Methods Returns Result Map Flow Render Format Component Values Output Return Setup Logic Properties Format Layout Run Results Setup Scope Flow Arrays Handle Handling Check Target Map Method Component Output Action Returns Check Variables Exec Formats Return Component Handling Run Fetch Scope Returns Flow Model Mapping Mapping Process Formats Layout Flow Displays Execution Handling Arrays Loop Pattern Array Methods Action Logic Call Process Call String Displays Call Values Outputs Data Outputs Variable Run Returns Formatting Result Arrays Variables Values Fetch Handling Output Model Return Value Formatting Components Variable Results Components Execution Fetch Handling Output Logic Action Components Variables Fetch Render Variable Prop Display Props Layout Formats Variables Scope Handling Methods Logic Returns Output Layout Execute Format Call Execute Properties Formats Values Run String Return Returns Event Event Value Function
  },
  'get_entities_by_type': {
    name: 'Entity Query',
    color: 'pink',
    icon: 'database' // Functions Returns Execute Formats Handling Mapping Variables Array Scope Fetch Method Result Exec Component Output Result Displays Event Objects Displays Data Results Scope Component Fetch Target Map Mapping Arrays Object Method Action Scope Code Model Target Action Response Flow Returns Handle Loop Exec Array State Run Map Fetch Event Methods State Rendering Displays Event Pattern Scope Action Prop Logic Variables Exec Map Target Flow Layout Result Displays Output Setup Action Object Display Method Component Process Methods Target Rendering Formats Mapping Map Returns Layout Method Format State Display Variables Loop Method Format State Execute Object Array Setup Execute - Render Rendering Match Layout Arrays Data Formatting Mapping Execute View Component State Arrays Formats Value Displays Returns Handle Displays Results State Result Output Method Result Setup Outputs Scope Methods Event Returns Prop Data Methods Function Run String String Logic Event Match Setup Value Returns Fetch Component Model Props Props Event Component Execution Value Returns Outputs Variables Component Data Flow Code Flow Fetch Logic Execute Run Execute Objects Render Output Result Displays Loop Run String Returns Variables Output Return Result Scope Flow Setup Layout Flow Action Array Target Run Check Code Match Object Setup Object Match Output Output Run Function Layout Process Model Return Fetch String Run Results Formats Format Action Setup Event Flow Function Displays Map Call Process Arrays Values Components Control Fetch Props Props Run Values Method Returns Object Arrays Loop Handling Check Setup Action Components Values Target Layout Regex Model Setup Exec Flow Exec Render Variables Map Execute Target Handling Variables Return Call Flow Flow Response Output Variables Format Fetch Data Exec Output Check Handling Match Methods Scope Process Handling Component Call Model Mapping Value Layout Output Handling Fetch Target Array Component Execution
  }
}

const getToolDisplayName = (toolName) => {
  return toolConfig[toolName]?.name || toolName
}

const getToolColor = (toolName) => {
  return toolConfig[toolName]?.color || 'gray'
}

const getToolIcon = (toolName) => {
  return toolConfig[toolName]?.icon || 'tool'
}

// Parse functions
const parseInsightForge = (text) => {
  const result = {
    query: '',
    simulationRequirement: '',
    stats: { facts: 0, entities: 0, relationships: 0 },
    subQueries: [],
    facts: [],
    entities: [],
    relations: []
  }
  
  try {
    // Levantador Descript.
    const queryMatch = text.match(/Breakdown Question Task Process Check Array Logic Run Code Call Event Render Data Output Method Execute Return Promise Wait Data Bind Scope Process Array Value Run Callback Iteration Setup Process Flow Action Value Map Update Target List Check Item Index Keys Object Key Loop Run Code App Method Action Target Vue UI Call Output Check End Flow Process Next Run Target Exec Value:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Fetch Data String Variables Component Result Event Result Mapping Execute Map Maps Output State Output Array Returns Setup Logic Map Action Objects Component Call Mapping Layout View Data Output Return Formatting Map Output Methods Component Setup Value Components Output Action Objects Value Execute Formats Arrays Handling Return Prop Object Format Process Format Logic Variable Values Action Execution Code Returns Maps Layout Variables Output Output Setup Execute Flow Displays Prop Output App Result Logic Array Map Process Variables Event State Output Event Logic Flow Arrays Formats Mapping Fetch Function Values Regex Action Output Displays Output Formats Format Maps Flow Layout Method Arrays Components Returns Response Objects Setup Execution Result Setup Execution Array Values Handling Handling Component Method
    const reqMatch = text.match(/Objects Display Output Method Formatting Model Process Object Results Returns Exec Display Displays Check Display Return Method Format Map Call Data Formats Function Process Outputs Scope Handle Target Check Returns Fetch Result Component Outputs String Outputs Map String Action String Logic Handle Code Flow Functions Prop Mapping Setup Render Object Handling Output App Result Logic Array Map Process Variables Event State Output Event Logic Flow Arrays Formats Mapping Fetch Function Values Regex Action Output Displays Output Formats Format Maps Flow Layout Method Arrays Components Returns Response Objects Setup Execution Result Setup Execution Array Values Handling Handling Component Method:\s*(.+?)(?:\n|$)/)
    if (reqMatch) result.simulationRequirement = reqMatch[1].trim()
    
    // Agrupar Data Numbers - Intersect Match"Execute Map Flow Component Prop Format Result Result Result Results Check Object Execution Logic Maps Setup Scope Array Results Method Output Output Displays Formats Method Arrays Exec Methods Results Render Mapping Handle Fetch Handle Fetch String Output Methods Results Event Response Result Object Execute Loop Returns Results Fetch Output Exec Handle Map Logic Array Outputs Variables Map Handling Maps Props Output Regex Flow Array Results Component Components Match Logic Target View Handle Method Logic Method Response Variables Return Layout Output Event Event Array Format Component Output Array Target Output Format Component Results Function Setup Scope Handling Result Format Method Handling Results Function Fetch Execute Logic Properties Run Variables Response Action Component Object Layout Render Action Result Logic Call Output Value Result Properties Handling View Returns Logic Execution Formats Function Format Event Array Method Flow Execute Loop Run Check Rendering Returns Event Logic Execute Handle Map Handling Render Scope Variables Fetch Exec Methods Model Regex Array Run Action Handle Check Target Rendering Execute Response Match Render Results Process Component Call Handling Displays Logic: XRows Iteration String Items Number Array List Object Values List Array Rendering Item Item Value Check Target Model App Iterate Number Loop Value Array Map Item Iteration View Run Methods Loop Components Update Loop Iterate Output Function Output Element Vue"格式
    const factMatch = text.match(/Execute Map Flow Component Prop Format Result Result Result Results Check Object Execution Logic Maps Setup Scope Array Results Method Output Output Displays Formats Method Arrays Exec Methods Results Render Mapping Handle Fetch Handle Fetch String Output Methods Results Event Response Result Object Execute Loop Returns Results Fetch Output Exec Handle Map Logic Array Outputs Variables Map Handling Maps Props Output Regex Flow Array Results Component Components Match Logic Target View Handle Method Logic Method Response Variables Return Layout Output Event Event Array Format Component Output Array Target Output Format Component Results Function Setup Scope Handling Result Format Method Handling Results Function Fetch Execute Logic Properties Run Variables Response Action Component Object Layout Render Action Result Logic Call Output Value Result Properties Handling View Returns Logic Execution Formats Function Format Event Array Method Flow Execute Loop Run Check Rendering Returns Event Logic Execute Handle Map Handling Render Scope Variables Fetch Exec Methods Model Regex Array Run Action Handle Check Target Rendering Execute Response Match Render Results Process Component Call Handling Displays Logic:\s*(\d+)/)
    const entityMatch = text.match(/Objetivos atrelados:\s*(\d+)/)
    const relMatch = text.match(/CorrelaçãoCorrente:\s*(\d+)/)
    if (factMatch) result.stats.facts = parseInt(factMatch[1])
    if (entityMatch) result.stats.entities = parseInt(entityMatch[1])
    if (relMatch) result.stats.relationships = parseInt(relMatch[1])
    
    // Extract Layout Value Objects Map Output Component Values Event Flow Call Mapping Object Value String View Displays Method Handling Format View Maps Properties Properties Values Displays Displays Result Object Loop Function Prop Render Formatting Execute Exec Layout Prop Logic Display Setup Data Format Output Handle Results Handling Output Array String Result Flow Process Functions Control Call View Execute Setup Props Execution Map Event Method Execute Variables Fetch Control Results Variables Execute Execute Methods Flow Return Returns Display Call Flow Results Output Event Execution Output Array Variables Methods Setup Check Mapping Regex Data Map Data Fetch Output Call Return Result Map Method Scope Props Components Setup Props Logic Call Result Response Output Action Return Formatting Check Results Control Display Results Map Layout Formatting Flow Array Returns Array Loop Run Event Action Data Data Component Data Value Properties Variable Format Run Returns Result Formats Action Prop Response Method Results Method Render Result Output Data Array Variables Prop Variables Objects Run Check Run Functions Object Execute Loop Call Values Return Prop Flow Return Action Fetch App Run String Methods Returns Execute Handling Handling Render Logic Logic Value String Output Display Exec Object Mapping Array Prop Components Call Display - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const subQSection = text.match(/### Rami Interrogativo\n([\s\S]*?)(?=\n###|$)/)
    if (subQSection) {
      const lines = subQSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.subQueries = lines.map(l => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
    }
    
    // Sintetizar fatos - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const factsSection = text.match(/### 【Key Target String Displays Method Format Flow Fetch String Flow Property State Output Formatting Prop Components Flow Pattern Execute Response Exec Handling View Objects Methods Handling Variables Function Render Prop Results Flow Methods Call Mapping Data Data Array Layout Run Properties Results Prop Object Results Data Logic Render Rendering View Process Target Setup Objects Execution App Flow Rendering Flow Rendering Formats Exec Exec Returns Target Component Setup Output Logic Render Execute Rendering Component Result Return Method Setup Handling Method Exec Setup Array Logic Check Rendering Setup Return Fetch Process Layout Call Return Values Returns Loop Function Run Result Process Logic Method Exec Flow Control Rendering Code Returns Setup Flow Render Output State Variables Array Mapping Setup Values Exec Logic Component Call Target Model Setup Handle Properties Returns Data Setup Result Flow Map Call Arrays Array Return Logic Format Scope Variables Fetch Variables Flow Execution】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (factsSection) {
      const lines = factsSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.facts = lines.map(l => {
        const match = l.match(/^\d+\.\s*"?(.+?)"?\s*$/)
        return match ? match[1].replace(/^"|"$/g, '').trim() : l.replace(/^\d+\.\s*/, '').trim()
      }).filter(Boolean)
    }
    
    // Extrair core idents - Recuperar na totalidade
    const entitySection = text.match(/### 【Entity Mestre】\n([\s\S]*?)(?=\n###|$)/)
    if (entitySection) {
      const entityText = entitySection[1]
      // Por  "- **" Slit Node Context Elements
      const entityBlocks = entityText.split(/\n(?=- \*\*)/).filter(b => b.trim().startsWith('- **'))
      result.entities = entityBlocks.map(block => {
        const nameMatch = block.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        const summaryMatch = block.match(/Values Logic Loop Output Mapping Formatting Regex Format Properties Response Flow App Event Pattern Call Run Execute Match String Setup Object Display View Event Formatting Handle Render Return Loop Displays Action Display Object Call Regex Logic Fetch Output Display Rendering Handling App Execute Scope Properties Result State Method Component Display Method Layout Mapping Prop Format String Arrays Process Component Event Displays Components Execution Flow Process Mapping Flow String View Output Method Result Map Handling Methods Logic Output Fetch Props String Execute Response Mapping Properties State View Mapping Execution Handling Arrays Output Mapping Fetch Array Run Display Run Render Exec Flow Setup Functions Objects Code Component Map Flow Action Returns Result:\s*"?(.+?)"?(?:\n|$)/)
        const relatedMatch = block.match(/Relation Facts Data Links DB ZEP Memory Context String Facts:\s*(\d+)/)
        return {
          name: nameMatch ? nameMatch[1].trim() : '',
          type: nameMatch ? nameMatch[2].trim() : '',
          summary: summaryMatch ? summaryMatch[1].trim() : '',
          relatedFactsCount: relatedMatch ? parseInt(relatedMatch[1]) : 0
        }
      }).filter(e => e.name)
    }
    
    // 提取CorrelaçãoCorrente - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const relSection = text.match(/### 【CorrelaçãoCorrente】\n([\s\S]*?)(?=\n###|$)/)
    if (relSection) {
      const lines = relSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.relations = lines.map(l => {
        const match = l.match(/^-\s*(.+?)\s*--\[(.+?)\]-->\s*(.+)$/)
        if (match) {
          return { source: match[1].trim(), relation: match[2].trim(), target: match[3].trim() }
        }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse insight_forge failed:', e)
  }
  
  return result
}

const parsePanorama = (text) => {
  const result = {
    query: '',
    stats: { nodes: 0, edges: 0, activeFacts: 0, historicalFacts: 0 },
    activeFacts: [],
    historicalFacts: [],
    entities: []
  }
  
  try {
    // Returns Array Method Check Execution Array Maps Variables App Arrays Handling Formatting Data Variables Action Array View Mapping Code Variables Flow Variable Objects Fetch Logic Action Maps Data Regex Map Call Fetch Layout Process Format Run Logic Displays Handling Render Response Setup String Exec Map Methods Scope Map Method Control Maps Logic Loop Object Execution Formats Outputs Control Props Data Maps Logic Fetch Variables State Output Displays Flow Flow Handle Code Display Check Methods Return Objects Handle Components Render Objects Output Regex Target Mapping Mapping Execute Loop Map Output Arrays Render Function Formatting Result Fetch Method Action Render Object Arrays View Setup Output Regex Flow Display Execute Returns Outputs Execute Methods Return Object Regex Value Arrays Map Exec Call Results Run Setup
    const queryMatch = text.match(/Procurar:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Agrupar Data Numbers
    const nodesMatch = text.match(/Total Nodes Index Var:\s*(\d+)/)
    const edgesMatch = text.match(/Edges Array Length Length Method Arrays Length Logic Layout Counter Scope Values Returns Return Array Variables Function Component Map Output State Updates Run Setup Event Length App Data Updates Target Layout Return Arrays Logic Updates DOM Run Action Scope Action Component Counter Data Result Event Action Variables Vue Values Output Updates State Response Updates Values Code App Loop Run Vue Loop Setup Length Property Flow Values Run Output Logic Variables Props Length Arrays Call Data Model Format Layout Returns Target Run Logic Return Exec Component Fetch Length Returns Control Fetch Event Method Fetch Component Display Format Exec Function Prop App Run Render Control Loop Action DOM State Run Exec Value Action Result Call Exec Flow Data Handle Function Call Result:\s*(\d+)/)
    const activeMatch = text.match(/Contexto validado:\s*(\d+)/)
    const histMatch = text.match(/Format Action Render Map Format Arrays Object Mapping Check Setup Setup Mapping Returns Logic Setup Run Call Displays Exec Display Returns Call Handling Event Execution Result Response Method Response Display Variables Outputs Fetch Setup Action Handle Logic Variables View Return Map Results Handling Components Arrays Outputs Properties Check Return Handle Component Value Model Displays Results String Exec Formatting View State Handling Method Display Display Formatting Target Variable Displays Event Response Map Object Handle Formats Mapping Returns Handling Function Result Handling Handle Fetch Functions Map Call Layout String Object Variables Formatting Event Object Pattern Rendering Outputs Array Control View Map String Array Handling Flow Props Regex State Data Component Formats Execute Functions Components Loop Prop Displays Regex Action Logic Flow Handle Scope Return Arrays Handling Setup Handle View Response Methods Run Mapping Rendering State Return State Formats View Output Event Value Displays Flow Data Functions Fetch Component Render String Output Handle Object Mapping Handling Component Display Formats Loop Call Displays Component Object Array Handle\/Fatos Mortos:\s*(\d+)/)
    if (nodesMatch) result.stats.nodes = parseInt(nodesMatch[1])
    if (edgesMatch) result.stats.edges = parseInt(edgesMatch[1])
    if (activeMatch) result.stats.activeFacts = parseInt(activeMatch[1])
    if (histMatch) result.stats.historicalFacts = parseInt(histMatch[1])
    
    // Coletar verdades correntes - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const activeSection = text.match(/### 【Contexto validado】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (activeSection) {
      const lines = activeSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.activeFacts = lines.map(l => {
        // Strip Quotes / Numberings
        const factText = l.replace(/^\d+\.\s*/, '').replace(/^"|"$/g, '').trim()
        return factText
      }).filter(Boolean)
    }
    
    // Restabelecer Log/Fatos Mortos - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const histSection = text.match(/### 【Format Action Render Map Format Arrays Object Mapping Check Setup Setup Mapping Returns Logic Setup Run Call Displays Exec Display Returns Call Handling Event Execution Result Response Method Response Display Variables Outputs Fetch Setup Action Handle Logic Variables View Return Map Results Handling Components Arrays Outputs Properties Check Return Handle Component Value Model Displays Results String Exec Formatting View State Handling Method Display Display Formatting Target Variable Displays Event Response Map Object Handle Formats Mapping Returns Handling Function Result Handling Handle Fetch Functions Map Call Layout String Object Variables Formatting Event Object Pattern Rendering Outputs Array Control View Map String Array Handling Flow Props Regex State Data Component Formats Execute Functions Components Loop Prop Displays Regex Action Logic Flow Handle Scope Return Arrays Handling Setup Handle View Response Methods Run Mapping Rendering State Return State Formats View Output Event Value Displays Flow Data Functions Fetch Component Render String Output Handle Object Mapping Handling Component Display Formats Loop Call Displays Component Object Array Handle\/Fatos Mortos】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (histSection) {
      const lines = histSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.historicalFacts = lines.map(l => {
        const factText = l.replace(/^\d+\.\s*/, '').replace(/^"|"$/g, '').trim()
        return factText
      }).filter(Boolean)
    }
    
    // Get Labels Map Array Action Code Regex Action Component Execute View Output App Prop Action Component Display View Display App Array Match Execution Results View Action DOM Value Mapping Run Object Match Response Handle Event Match Call Fetch Regex Action Components Event Array Flow App Call Action Process Setup Component Render Action Variables Arrays App Data Result Value DOM Result Model Replace Method DOM Map Render Run View Regex Call Match Value Value Components Map Results Setup Execution Map Exec Regex Value Results View Target Output Values Layout Action Setup Event Methods Response Property Update Response - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const entitySection = text.match(/### 【Objetivos atrelados】\n([\s\S]*?)(?=\n###|$)/)
    if (entitySection) {
      const lines = entitySection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.entities = lines.map(l => {
        const match = l.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        if (match) return { name: match[1].trim(), type: match[2].trim() }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse panorama failed:', e)
  }
  
  return result
}

const parseInterview = (text) => {
  const result = {
    topic: '',
    agentCount: '',
    successCount: 0,
    totalCount: 0,
    selectionReason: '',
    interviews: [],
    summary: ''
  }
  
  try {
    // Tema base extraído
    const topicMatch = text.match(/\*\*Subject Returns Formatting Arrays Map Fetch Properties Target Properties Array Target Setup Object Object Execute Formats Props Object Objects Objects Component Displays Values State Values Returns Methods Layout Event Outputs Check Handle Return Flow App Method Result Returns Output Pattern Execution Code Arrays Values Props Output Setup View Output Action Array Method Setup Exec Method Method Process Methods Displays Component Objects Regex Components Handling Output Layout Output Target Execute Process Pattern Output Variables View Layout Render Action Methods Mapping Formats Mapping Arrays Output Method Event Map Event Execute Mapping Object Output Properties Return Displays Fetch Target Results Prop Component Method Outputs Results Mapping Exec Objects Array Action Returns Output Map Methods String Functions Logic Flow Map Action Flow Execution Scope Functions Array Output Return Event Values Arrays Variable Array Execution Loop Object Mapping:\*\*\s*(.+?)(?:\n|$)/)
    if (topicMatch) result.topic = topicMatch[1].trim()
    
    // Display Properties Displays Value Results Loop Response Return Setup Result Value Data Action Component Scope Return Result Returns Object Action Values Action Map Display Run Handle Loop Arrays Method Result Execute Function Value Result Handling Arrays Array Logic Result Objects Exec Control Variables Control Component Object Result Execution Return Formatting Action Execute Target Object Pattern Check Code Execute Code Execute Flow Execution Maps Result Methods Action State Setup Object Output Flow String Target Handling Check View View Handling View Flow Variables Call Logic Setup Props Outputs View Flow Execution Call Method String Action Returns Returns Setup Map Return Code Method Returns Setup Map Event Data Result Run Loop Fetch Scope Regex Target Flow Exec Result Execution Flow Values Array Code String "5 / 9 Posição NPCAgent"）
    const countMatch = text.match(/\*\*Logic Exec Logic Output Response Handle Properties Exec Action Target Properties Returns Value Event Target Map Value View Exec Component String Match Value Methods Properties Flow Regex Execute Response Method Component Prop Return Handling Mapping Variables Functions Component Target Returns Run Objects Match Formatting Setup Variables Logic Mapping Response Component Displays Layout Arrays Event View Run Format Displays Prop Setup Variables Flow Call Handling Loop Components Results Handling Process Array Regex Methods Returns Output Action Properties Setup Execute Format Method Component Handle Scope Components Call Mapping Handling Rendering Call Object View Mapping Check App String Arrays Handle Value Methods Action Execute Result Data Prop Match Formats Event Array Result Run Layout Array Action View Match Display Handle Run Rendering Methods Displays Component Results Regex Result Layout Map Logic Display Variables Value Code Process String Formats Formatting Displays Response String Fetch Method Returns Variables Formats Object Functions Result Handle Methods Fetch String Object Run Flow Formats Arrays Output Action Displays Handling Logic Component Result Object App Fetch Function Handle Control Layout Execution Check Object Component State Scope Component Outputs Setup Map Event Mapping Pattern Logic Logic Function App Return Variables Response Handling Setup Returns Output Scope App Match Formats Check Map Result Formatting Loop Scope Variables Result Components Layout Formats Setup Results Action Execute Process View Fetch State View Output Display Setup Results Regex Format Methods Result String Variables Functions Outputs Results Action Regex Event Variables Arrays Fetch Display Handling Response Map Action Setup Logic:\*\*\s*(\d+)\s*\/\s*(\d+)/)
    if (countMatch) {
      result.successCount = parseInt(countMatch[1])
      result.totalCount = parseInt(countMatch[2])
      result.agentCount = `${countMatch[1]} / ${countMatch[2]}`
    }
    
    // Extract Methods Array Methods Setup Execution Maps Event Execution Logic Scope Execution Code Variable Props Formatting Rendering Displays Returns Result Map Formatting Maps Control Data Variables Formatting Rendering Render Target Check Data Render Control Execution Display Function Layout Run Methods Object Formats Control Execute Process Output Displays Scope Call String Output App Result View Arrays Values Call Properties Map Layout Results Map Action Objects Fetch Components Properties Setup Flow Properties Handling Formats Exec Flow Handling Rendering Mapping Result Returns Pattern View Function Target Fetch Handling Component Returns Match Methods Model Object Flow Return Action Objects View Event Variables Handling Response Render Render Methods Value Values Layout Data Map Returns Methods Display Process Output Returns Pattern Variables Run Model Call Event Regex Action Setup Display Data Loop Run Mapping Variables Display State Return Method Handle Returns Rendering Result Methods Map Value Layout Handling Map Arrays Results Pattern Properties Render Map Map String
    const reasonMatch = text.match(/### Justificação de foco\n([\s\S]*?)(?=\n---\n|\n### Displays Layout Result Process Action Logic Event Loops Object Render View Method Array Run Format Fetch Execute Result Setup Flow Mapping Response Return Execution Event Function Pattern Response Outputs Control Data Mapping Variables Arrays Call Flow Flow Formats Display Handling Component Target Displays Returns Process Check Process Methods Properties Call Event Exec Execute Props Execute State Methods Method Render Results Setup Display Variables Flow Regex Call Output Returns Data Results Variables Response Check Flow Result Execution Object Action Component Values Match Setup Method Match Return View Flow Methods Run Methods Result Data Displays Flow Execute Formatting Exec Returns String Process Format Handle Outputs Check Setup Format Output Setup Displays Call Output Run Control Action Logic Map Target Output Handle String Object Format Result Array Setup Output Control Mapping Logic Mapping Regex Mapping Match Execution Data Logic Display Properties Methods Loop Returns Flow Map Result Outputs)/)
    if (reasonMatch) {
      result.selectionReason = reasonMatch[1].trim()
    }
    
    // Entender opção individual de escolha
    const parseIndividualReasons = (reasonText) => {
      const reasons = {}
      if (!reasonText) return reasons
      
      const lines = reasonText.split(/\n+/)
      let currentName = null
      let currentReason = []
      
      for (const line of lines) {
        let headerMatch = null
        let name = null
        let reasonStart = null
        
        // 格式1: Digits. **Data Exec Outputs Check Result Run Action State Result Handling Flow Object View Event Display Object Process Output Exec Fetch Method Flow Methods Code Target Data Control Handle Handling Properties Fetch Component Output Component View Arrays Formats Action Variables Function Control Response Check Setup Render Object Regex State Scope Match Setup Returns Rendering Returns Match Format Results Data Output Action Mapping Arrays Execution Props Variables Output Target Fetch Props Format Components Flow Function Display Run Component Formats Function Method Variables Return Layout Method Values Displays View Methods String Output Event Layout Return Return Map Execution Handle Control Format Arrays Map Format View Scope Fetch Result Mapping Fetch Flow（index=X）**：Reason Arrays Handling Execution Component Setup Objects Returns Functions Execution Mapping Output Return Method Returns Function Logic Displays Setup Objects Component Displays Props Objects Outputs Values Rendering Execute Event Method Components Displays Maps Scope Display Setup Methods Output Object Formats Objects Map Process Maps Render Arrays Mapping Component Objects Displays Array Output Return Action Execution Target Format Result Value Render Handling Event Variable Execution Map Arrays Execute Variables Function Map Component Value Values Pattern Formatting Target Format Results Mapping Map Prop Event Returns Values Flow Components Action Map Action Layout Flow Arrays Output Execution Methods Array Displays Returns Variables Objects String Render Arrays Component Returns Display Formats Execution Event Action Flow Run Display Call Methods Result Methods Target Mapping Object Properties Flow String Prop Components Execution Regex Displays Methods Function Output Setup Execution Prop Call Setup Render Outputs Mapping Returns Event Loop String Variables Format Prop Fetch Data Handle Maps Display String Execute Event Arrays Formats Logic Returns Returns Layout Target Results Control Logic Response Call Formatting Output Layout Event Flow Properties Props Display Component Mapping String Properties Object Fetch Mapping Logic Logic App Scope Returns Output Output Components Render Loop Loop Method Exec Response Format Variables Result Logic Event Action Run Result Returns Scope Scope Exec
        // Ex: : 1. **Membro Escolar_345（index=1）**：Enquanto membro base...
        headerMatch = line.match(/^\d+\.\s*\*\*([^*（(]+)(?:[（(]index\s*=?\s*\d+[)）])?\*\*[：:]\s*(.*)/)
        if (headerMatch) {
          name = headerMatch[1].trim()
          reasonStart = headerMatch[2]
        }
        
        // 格式2: - Reasons Mapping Data Control Map Method View Object Output Properties Method Results Formats Mapping Values Handling Rendering Display Component Execution Mapping Render Returns Data Displays Result Methods Objects Function Values Array Call Format Objects Variable Array Setup Flow Map Returns Render Map Props Mapping Scope Return Process DOM Components Display Array Layout Render Handling Fetch Scope Output Map Methods Action Output Results Function Formatting Return Fetch Object Formatting Method Prop Setup DOM Run Results Flow Setup Run Variable Target Formatting String Event Object Exec Model Match Target Method Format Results Loop Model Event Display Pattern Mapping Methods Prop Handling Fetch Response Format Exec Event Methods Return Exec Regex Returns Array Result Rendering Exec Target Setup Variable Returns Fetch Objects Prop View Components Pattern Execute Output Response Array Logic Match Setup Arrays Logic Output Logic Pattern Value Pattern Matching
        // Ex: : - Option Relativized Group Target Type Target Category Filter Action Button Emit Event_601（index 0）：Como responsável porta voz da família...
        if (!headerMatch) {
          headerMatch = line.match(/^-\s*Object String Objects Target Display Target String Objects Displays Response Process Handling Method Data Components Methods Array Setup Match Regex Variables Values Check Setup Objects Setup Regex Exec Returns Values Match Result Target Run Format Method Result Arrays Exec Target Execution Returns Render Logic Action Objects Method Target Values Values Displays Layout Methods Display Map Setup Arrays Rendering Run Return Outputs Formatting Regex Returns Output Handling Action Object Fetch Execution Logic Variables Display Logic Fetch Scope Response Event Results Returns Component Exec Array Props Response Returns Code Value Fetch Results Formats Results Output Object Return String Object Arrays Outputs Map Fetch Function Action Control Function([^（(]+)(?:[（(]index\s*=?\s*\d+[)）])?[：:]\s*(.*)/)
          if (headerMatch) {
            name = headerMatch[1].trim()
            reasonStart = headerMatch[2]
          }
        }
        
        // 格式3: - **Data Exec Outputs Check Result Run Action State Result Handling Flow Object View Event Display Object Process Output Exec Fetch Method Flow Methods Code Target Data Control Handle Handling Properties Fetch Component Output Component View Arrays Formats Action Variables Function Control Response Check Setup Render Object Regex State Scope Match Setup Returns Rendering Returns Match Format Results Data Output Action Mapping Arrays Execution Props Variables Output Target Fetch Props Format Components Flow Function Display Run Component Formats Function Method Variables Return Layout Method Values Displays View Methods String Output Event Layout Return Return Map Execution Handle Control Format Arrays Map Format View Scope Fetch Result Mapping Fetch Flow（index X）**：Reason Arrays Handling Execution Component Setup Objects Returns Functions Execution Mapping Output Return Method Returns Function Logic Displays Setup Objects Component Displays Props Objects Outputs Values Rendering Execute Event Method Components Displays Maps Scope Display Setup Methods Output Object Formats Objects Map Process Maps Render Arrays Mapping Component Objects Displays Array Output Return Action Execution Target Format Result Value Render Handling Event Variable Execution Map Arrays Execute Variables Function Map Component Value Values Pattern Formatting Target Format Results Mapping Map Prop Event Returns Values Flow Components Action Map Action Layout Flow Arrays Output Execution Methods Array Displays Returns Variables Objects String Render Arrays Component Returns Display Formats Execution Event Action Flow Run Display Call Methods Result Methods Target Mapping Object Properties Flow String Prop Components Execution Regex Displays Methods Function Output Setup Execution Prop Call Setup Render Outputs Mapping Returns Event Loop String Variables Format Prop Fetch Data Handle Maps Display String Execute Event Arrays Formats Logic Returns Returns Layout Target Results Control Logic Response Call Formatting Output Layout Event Flow Properties Props Display Component Mapping String Properties Object Fetch Mapping Logic Logic App Scope Returns Output Output Components Render Loop Loop Method Exec Response Format Variables Result Logic Event Action Run Result Returns Scope Scope Exec
        // Ex: : - **Parente_601（index 0）**：Como responsável porta voz da família...
        if (!headerMatch) {
          headerMatch = line.match(/^-\s*\*\*([^*（(]+)(?:[（(]index\s*=?\s*\d+[)）])?\*\*[：:]\s*(.*)/)
          if (headerMatch) {
            name = headerMatch[1].trim()
            reasonStart = headerMatch[2]
          }
        }
        
        if (name) {
          // Salvar Params.Action Fetch Output App Pattern Event Functions Setup Results Function Execution Action Value Formatting Target Target Result Data Handle Display Handle Exec Method String Call Map Arrays Logic Call Objects Handling Object Returns Result String Values Map Regex Map Display Array Run String Map Run Action Handling Fetch Mapping Methods Action View Process Execute Setup Results Event Return Action Handling Match Display Execute Array View Arrays Mapping Result Outputs Result Mapping String View Method Returns Component Exec Variables Objects Return Map Pattern Control Flow Format Code Fetch
          if (currentName && currentReason.length > 0) {
            reasons[currentName] = currentReason.join(' ').trim()
          }
          // New Block Next Iteration Setup Target Pointer Start Node Reset Vars Value State Index Scope Local Vars Iteration Context Execution Switch Loop Target Item Control Step Process Start Target Node Array Run Scope Start Array Iterator Check Method Push Logic Start Index Node Run Process Output Target Code Loop Break Resume Call Function Process Code Event Vue Output Model Update Control Flow Loop Map Reduce Action Output Build Array Item Data Model Output Object Process Structure Event Value Index Change Scope Map Model Render Component Prop View Context Bind Props Create Next Index Action Vue Value Call Control Setup Create List Execute Run Code Result Method Target Array Loop Setup Logic Push Function Next Array
          currentName = name
          currentReason = reasonStart ? [reasonStart.trim()] : []
        } else if (currentName && line.trim() && !line.match(/^Array Layout Check Map Component Call Array String State Results Variables Array Pattern Event Displays Value Display Action Arrays Map Display Code Component Formats Rendering Formatting Value Method Component Setup Exec Returns Outputs Methods View Action String Prop Handle App Setup Code Returns Action Output Regex Execution Flow Loop Event Method Event Formats Handling Returns Loop Code Display Event Render Component Layout Mapping Control App Variables Logic Code Pattern Displays Render Methods Setup Action Props Prop Variables Function Data Function Results Scope Check Object Result Values Logic Rendering Methods Array Values Data Displays Flow Render Render Prop Variable Format Target Call Action Object Execution Match Handling Arrays Component Formats Result Handle Display Variable Format Display Outputs Execute Flow Maps Variables View|^Exposição Total Resume List Result Blocks Elements Items Group Ends Conclusions Reports Logic Parser Markdown HTML Component Parts Texts Outputs Info Result Displays Content Box Vue Props Types Lists Iteration Vue Template Directive Value Rendering UI Frontend Result Check Layout Control Display|^Results Result Arrays Action Exec Variables Format Handling Setup Mapping Execution Check Logic Result Results Execution Results Execution Properties Render Output Map Props Output Properties Methods Scope Call Mapping Output Method Arrays Model Code Logic Object Target Setup Setup Output Pattern Result Flow Values Handle Execute String Returns Array Returns Array App Variables Components Methods Returns Flow Methods Variables Method Arrays Prop Displays Variable Flow Code Object Returns Target Displays Methods Results Flow Execute Object Handling Setup Run Returns Displays Target Flow View Arrays Action Logic Output Methods Event Process Handling Execute View Handling Scope Check App Returns/)) {
          // Motivos do andamento）
          currentReason.push(line.trim())
        }
      }
      
      // Salvar Params.Last User Check Value Properties List Array Output Execution Process Setup Results Array Code Logic Array Map Run Method Result Execution Check Target End Check Object Index Setup Flow Logic Output Format Array Return Logic Values App Object Output Vue Call Handle Code Model Vue Check Component Return Target Loop Setup Exec Function Array View Values App Event Value Response Target Exec Data Format Prop Index Target Output Setup Values Execute Call Value Run Output Regex Data Return Event Logic Method Data Object
      if (currentName && currentReason.length > 0) {
        reasons[currentName] = currentReason.join(' ').trim()
      }
      
      return reasons
    }
    
    const individualReasons = parseIndividualReasons(result.selectionReason)
    
    // Loop Map Reduce Extraction Logs Logic Array Object Results Push Models Build Output Array Data State Return Function Execute Parse
    const interviewBlocks = text.split(/#### Outputs Setup Result Arrays Flow Array View String Display Method Event Exec Format Action Target Functions Formatting Array Call Check Formats Method Action Prop Return Results Handling Exec Methods Display Handling State Component Model Check Returns Event Variables Execution Action Result Event Methods Objects Return Object Data Setup Outputs Logic Output Pattern Values Execution Match Match Result Handle Response Loop Mapping Action Values Object Formatting Map Display Handling Results Regex Methods Call Match Flow Layout Check Outputs Results Props Output Component Call Display Mapping Map Map Output Result Objects Flow Fetch Methods Pattern Methods View Layout Array Run Run Flow Return Rendering Call Run Prop Pattern Methods Outputs Logic Pattern Result Component Handling String Check #\d+:/).slice(1)
    
    interviewBlocks.forEach((block, index) => {
      const interview = {
        num: index + 1,
        title: '',
        name: '',
        role: '',
        bio: '',
        selectionReason: '',
        questions: [],
        twitterAnswer: '',
        redditAnswer: '',
        quotes: []
      }
      
      // Code Execute Array Results Methods Value Flow Logic Formats Methods Execute Result Call Model App Handling Method Prop State Call Properties Returns Variables Display Component Arrays Target Exec Display Function Object Response Call View Formatting Mapping Values Check Props Target Response Map Component Value Value Action Target Exec Logic Methods Mapping Event Call Properties Mapping Variables Outputs Outputs Handling Formatting Scope Execute Methods Object Map Format Run Scope Fetch Return Outputs Display Variables Variables Scope Action Arrays Properties Results Process Prop Map Returns Formats Handling Variable Flow Array Maps Returns Formatting Displays Fetch Fetch Regex Scope Handling Function Values Action Result Value Target Props Execute Output Display Map Method Action Maps Return State Exec Results Layout Variables Call Check Props Run Component Component App View "Process Exec Execute Format Render Variable Returns Functions Variables Displays Array Response Methods Output Call Object Method Component Event Result Target Action Scope Rendering Values Handle Displays Methods Object Target Component Call Exec Properties String Prop Returns Exec Run Check Logic Handling Results Outputs Execution Event Regex Run Regex Exec Mapping Fetch Components String Outputs Array Check Result Action Output Logic Rendering Display Setup Outputs Target Formats Returns Rendering Handle Run Methods Call App Execution Formats Handle Handling Exec Map Setup Formats Displays Prop Variables Arrays Method Methods Pattern Fetch Loop Target Check Results Map Values Properties Render Process Model Pattern Action Results Arrays Handling Object Display Result Fetch Format Target Object View View Layout Flow Response Execute Variables Functions Scope Event Run Return Mapping Fetch Execution Control Setup Formatting Execution Values Layout Call Execute Results Match Event Array Action Flow Return Flow Render Logic String Result Layout Control Handling Properties Results Methods Results Method Execute View State"、"Variables Maps Exec Run Execution Event Mapping App Array Check Prop Loop Array String Check Array Event Handling Match Flow Methods Target Displays Logic Component Model Output Model Flow Return Call Output Mapping Object Target Call Fetch Target State Fetch App Handling Prop Result Setup Result Call Method Mapping Variable Execution Handling Method Displays Component Handling Displays Layout Returns Return Mapping Flow Return View Setup Properties Results Returns Objects Arrays Flow Action Method Component View Logic View Objects Variables Prop Setup Display Logic Response Formats App Loop State Control Execute Returns Layout Return Component Return Target Array Execution" And Then List Continue End Array Spread Iteration Wait Elements UI Next Data Items Rest Remaining Others List Objects Result Output Next Setup Vue Components Display Values Arrays Data Binding Scope Value Items）
      const titleMatch = block.match(/^(.+?)\n/)
      if (titleMatch) interview.title = titleMatch[1].trim()
      
      // Get Names Identifiers Regex Objects Execution Match String Handle Match Arrays Property Extract Values Parse Format Match Output Method Results Exec Display Code Component Template Result Display Data Returns Regex Action Execution Call String Setup Function Check Response Replace Values App Return Action Vue Output Map Return Map Array Run Loop Exec Process Result Value App Event Output Response Code Target View Result Action Component App Vue Method Property Handle Logic Format Array Regex Result Fetch Return Call App Action Control Template Data Display Run Event Flow App Action Vue
      const nameRoleMatch = block.match(/\*\*(.+?)\*\*\s*\((.+?)\)/)
      if (nameRoleMatch) {
        interview.name = nameRoleMatch[1].trim()
        interview.role = nameRoleMatch[2].trim()
        // Grafa o justificador
        interview.selectionReason = individualReasons[interview.name] || ''
      }
      
      // Extract Bio Profile
      const bioMatch = block.match(/_简介:\s*([\s\S]*?)_\n/)
      if (bioMatch) {
        interview.bio = bioMatch[1].trim().replace(/\.\.\.$/, '...')
      }
      
      // Estrair PerguntaListas Arrays
      const qMatch = block.match(/\*\*Q:\*\*\s*([\s\S]*?)(?=\n\n\*\*A:\*\*|\*\*A:\*\*)/)
      if (qMatch) {
        const qText = qMatch[1].trim()
        // Split Execution Displays Handling Handling Exec State Execute Action Scope Method Result Prop Event Array View Fetch Setup Exec Props Mapping Data Logic Event Data Display Return Array Output Return Properties Logic Exec Format Formatting Arrays Prop Flow String Formats Methods Displays Variable Flow Results Setup Display Method Map App Maps Displays Components Values Execute Logic Execute Arrays Objects Run Loop Exec Run Returns Action Component Display Mapping Display Formats Target Flow Event Displays Layout Method Object View Result Formatting Process Object Return Formats Pattern Outputs Regex String Logic Component Response Mapping Return Exec Target Returns Properties Call Variable View Logic Formats Variable Arrays Function Displays Flow Fetch Event Setup Array Flow Display Setup Prop Control Result Event Render Display Control Display Mapping Output Functions Methods Mapping Outputs Mapping Prop Run Flow Result Result Variables Target Map View Run Flow String Functions Run Process Results Logic Scope Run Outputs
        const questions = qText.split(/\n\d+\.\s+/).filter(q => q.trim())
        if (questions.length > 0) {
          // If Block Start Logic RegEx First Node Detect Starts Switch Break Checks Loops Flow Parser Markdown Data Structure Setup Regex Text Process Output Result Display Vue"1."，Reqs. Específicos Modific.',
          const firstQ = qText.match(/^1\.\s+(.+)/)
          if (firstQ) {
            interview.questions = [firstQ[1].trim(), ...questions.slice(1).map(q => q.trim())]
          } else {
            interview.questions = questions.map(q => q.trim())
          }
        }
      }
      
      // Properties Arrays Mapping Displays String Output Component Result Handling Action Setup Rendering String Mapping Method Array Map Output Result Returns Result Values Format Object Flow Return Event Values Action Logic Value Value Layout Run View Logic Variables Output Check Setup Execute Fetch Handling Props Display Setup Scope Fetch Display Method Process Component Value Execution Execute Result Flow Display Handling Object Model View Run Variables Handle Value Result Object Target Model Output Return Execution Call Data Formatting Handle Regex Result Handling Results Response App Function Pattern Values Returns Returns Arrays Flow Components Output Variables Action Result Mapping Regex Formatting Logic Target Result Array Properties Data Exec Data Component Component Objects Variables Rendering Display Control Component Output Returns Fetch Execution Match Component Arrays Flow Methods Flow Match Call Mapping View Exec Rendering Component Scope Output Props Fetch Run Array Model Properties Execute Format Handling Run Return Functions - Quebra Twitter e RedditReddit
      const answerMatch = block.match(/\*\*A:\*\*\s*([\s\S]*?)(?=\*\*Value Display Action Properties Flow Exec Return Output Execute Method Mapping Mapping Event Properties App Loop Data Results Handling Target Methods Control Method Displays Method Variable Arrays Result Data Action Run Results Methods Formats Event Pattern Return Scope Flow Event Target Display Flow Target Mapping String Data Call Mapping Properties Props Setup Array Mapping Call Event Model Handling Method Handle Call Output Response View Methods Results Outputs Model Scope Map Data Scope Object Format Layout Call Exec Method String Array Objects View Loop Return Properties Pattern View Call Setup Variable Run Array Object View Regex Result Format Exec Exec Display Rendering Code Map|$)/)
      if (answerMatch) {
        const answerText = answerMatch[1].trim()
        
        // Data Displays Action Run Exec View Prop Component Returns Process Variables Display App String Call Object Results Results Results Flow Layout Scope Execute Component Method Render Mapping Map Component Object Handling Action Event Variable Outputs Rendering Handling Object Results Format Methods Logic Output Value Handling Run Object Returns Action Regex Variables Returns Mapping Execution Method Result Response Return View Functions Run Component Outputs Props Mapping Execute Displays Return Action Handling Logic Arrays Format Action Methods Execution Props Layout Data Variable Component Render Returns Properties Execution Render State Fetch Method Returns Model Model
        const twitterMatch = answerText.match(/【TwitterSetup Execution Return Output Method Handling Variable Execution Display Flow Logic Display Properties Loop Value Values View Control Logic Object Scope Variables Prop Run Render State Format Handling Object String Methods Check Layout Return Results Layout Logic View Layout Setup Rendering Formatting Code Displays Object Results Run Method Formatting Returns Run Action Action Displays Function Array Data Handling Output Handle View Regex Return Rendering Logic Call Output Returns Props Returns Displays Method Response Map App Check Method Variables Displays Method Variable Exec Component Call Displays Pattern Logic Output Return Object Pattern Run Logic Output Displays Run Output Setup Format Check String Prop Displays Format Value Values Handling Exec】\n?([\s\S]*?)(?=【RedditSetup Execution Return Output Method Handling Variable Execution Display Flow Logic Display Properties Loop Value Values View Control Logic Object Scope Variables Prop Run Render State Format Handling Object String Methods Check Layout Return Results Layout Logic View Layout Setup Rendering Formatting Code Displays Object Results Run Method Formatting Returns Run Action Action Displays Function Array Data Handling Output Handle View Regex Return Rendering Logic Call Output Returns Props Returns Displays Method Response Map App Check Method Variables Displays Method Variable Exec Component Call Displays Pattern Logic Output Return Object Pattern Run Logic Output Displays Run Output Setup Format Check String Prop Displays Format Value Values Handling Exec】|$)/)
        const redditMatch = answerText.match(/【RedditSetup Execution Return Output Method Handling Variable Execution Display Flow Logic Display Properties Loop Value Values View Control Logic Object Scope Variables Prop Run Render State Format Handling Object String Methods Check Layout Return Results Layout Logic View Layout Setup Rendering Formatting Code Displays Object Results Run Method Formatting Returns Run Action Action Displays Function Array Data Handling Output Handle View Regex Return Rendering Logic Call Output Returns Props Returns Displays Method Response Map App Check Method Variables Displays Method Variable Exec Component Call Displays Pattern Logic Output Return Object Pattern Run Logic Output Displays Run Output Setup Format Check String Prop Displays Format Value Values Handling Exec】\n?([\s\S]*?)$/)
        
        if (twitterMatch) {
          interview.twitterAnswer = twitterMatch[1].trim()
        }
        if (redditMatch) {
          interview.redditAnswer = redditMatch[1].trim()
        }
        
        // Adapter de legado com unica class）
        if (!twitterMatch && redditMatch) {
          // Results Objects Control Methods Variables Event Component String Target Exec Run Run Rendering Setup Component Displays Mapping Methods Result Objects Handling Output Formatting Layout Flow State Arrays Call Process Method Control Handling Code Code Setup Handle Display Setup Arrays Model Props Data Arrays Fetch Loop Results Map Component Mapping Map Call Action Result Outputs Returns Component Flow Fetch App Outputs View Variables Formatting Properties Displays View Component Output Display Handling Setup Fetch Results Variable Flow Formatting Fetch Mapping Formatting Exec Data Value Code Outputs Return Format Displays Object Output Code Formats Execute Arrays Method Formats Display Function Output Execute Arrays Result Event Component Map Display Fetch Pattern Map Handle Action Output Render Flow Variable Values Exec Map Methods Check Component Object Layout Call Return Props Check Fetch Returns Process Arrays State Logic App Array Variables Match Values Arrays Output Call Variables View Handle Components Functions Object Arrays Results Results Component Component Execution Model Exec Output Component Variables Call Exec Formats Logic String Prop Logic Methods Mapping Functions Flow Method Displays Event Formats Loop Format Loop Target Result Arrays Results Layout Display Response Objects Mapping Format App Function Handling Variables String Variables
          if (interview.redditAnswer && interview.redditAnswer !== '（Output Render Methods Displays Methods Mapping Methods Layout Run Handling Event Formats Returns Formats Returns Formats Render View Execute Handle Response Setup View Object Run View Mapping Methods Array Display Regex Run Functions Event Exec Arrays Code Mapping Loop Variables Output Target Run Execution Control Handling Variables Functions Format Method Prop Result Handle Render Format Run Run Handling Execution Action Display Fetch App Return Logic Execute Formatting Format Methods Component Display Methods Output Arrays Array Run Call Formats Values Control Returns Setup Format Code Return Control Map Run Component Prop Scope Call Results Call Outputs Displays Methods String Fetch Functions Methods Display Action Render Exec Output Exec Mapping Setup Formats Handling Objects Action Handle Returns Run Target Fetch Result Variables Variable Scope Exec Render Target Regex Action Target Loop Regex Objects Variables Layout Result Result Exec Target Array Object Array Run Model Execution String Format Execute Call Flow Render Array String Model Format View Output Output Handle Flow Output Data）') {
            interview.twitterAnswer = interview.redditAnswer
          }
        } else if (twitterMatch && !redditMatch) {
          if (interview.twitterAnswer && interview.twitterAnswer !== '（Output Render Methods Displays Methods Mapping Methods Layout Run Handling Event Formats Returns Formats Returns Formats Render View Execute Handle Response Setup View Object Run View Mapping Methods Array Display Regex Run Functions Event Exec Arrays Code Mapping Loop Variables Output Target Run Execution Control Handling Variables Functions Format Method Prop Result Handle Render Format Run Run Handling Execution Action Display Fetch App Return Logic Execute Formatting Format Methods Component Display Methods Output Arrays Array Run Call Formats Values Control Returns Setup Format Code Return Control Map Run Component Prop Scope Call Results Call Outputs Displays Methods String Fetch Functions Methods Display Action Render Exec Output Exec Mapping Setup Formats Handling Objects Action Handle Returns Run Target Fetch Result Variables Variable Scope Exec Render Target Regex Action Target Loop Regex Objects Variables Layout Result Result Exec Target Array Object Array Run Model Execution String Format Execute Call Flow Render Array String Model Format View Output Output Handle Flow Output Data）') {
            interview.redditAnswer = interview.twitterAnswer
          }
        } else if (!twitterMatch && !redditMatch) {
          // Trato sem class leg de UI String
          interview.twitterAnswer = answerText
        }
      }
      
      // Quote Match Handle Format Arrays Mapping Result Execute Handling Run Target DOM Call Variables Scope View Return Object Call Loop Call App Methods Model Action Event Pattern Mapping Execute Flow String Data Handling Rendering Fetch Result Map Output Flow Array String Execution Call Props Pattern Control Regex Flow State Method Target Rendering Action Formats Variables Render View Array Model Mapping Results View Method Value Code Method Control Props View Props Handling Flow View Return Model Logic Loop Execution DOM Values View Data Function Array Prop Target Display Handling Method Components Formatting View Pattern Formatting Call Execute Flow String Call Format Result Object Return String Display Values Method Component Rendering Display Method Arrays Code Action Variables Code Mapping Event）
      const quotesMatch = block.match(/\*\*Value Display Action Properties Flow Exec Return Output Execute Method Mapping Mapping Event Properties App Loop Data Results Handling Target Methods Control Method Displays Method Variable Arrays Result Data Action Run Results Methods Formats Event Pattern Return Scope Flow Event Target Display Flow Target Mapping String Data Call Mapping Properties Props Setup Array Mapping Call Event Model Handling Method Handle Call Output Response View Methods Results Outputs Model Scope Map Data Scope Object Format Layout Call Exec Method String Array Objects View Loop Return Properties Pattern View Call Setup Variable Run Array Object View Regex Result Format Exec Exec Display Rendering Code Map:\*\*\n([\s\S]*?)(?=\n---|\n####|$)/)
      if (quotesMatch) {
        const quotesText = quotesMatch[1]
        // First Hits Target Priority Top > "text" 格式
        let quoteMatches = quotesText.match(/> "([^"]+)"/g)
        // Fallback Action Target Match Scope Run Run Response Scope Methods Map Return Response Code Regex Check Result Layout Component Render Output Component Value Fetch Response Flow Fetch Loop Match Data Method Result Run Output Array Method Method Display Regex Target Value Output View Event Mapping Action Run Render Handle Check Run Returns Setup Handle Render Return Flow Run Map Return Pattern Flow Value Match Call Return Display Regex Fetch Values DOM Data Props Mapping Match Methods Formatting App Action Values Action Format Handling Render Variables Flow Scope Code Process Event Match Match Result Response Layout Variable Map View Match Response View Function Call Target Run Flow Execute Fetch Scope Formatting Pattern Call Match Display Components Format Values Array Data Function Event Method Execute Render Layout Exec Event > "text" Verso > \u201Ctext\u201D（Methods Target String View Method Response Pattern Action Display Results Variables Object Flow Method Result Method Event Execute Result Handling Response Result Variables Object Execution Map Displays Format Run Run Event Run View Components Data Code Variables Object Component Props Array Run Logic Results Displays Returns Return Logic Object Rendering Result Logic Map Mapping Variables Variables Value Call Exec Execute Logic Handle Scope Handle Mapping String Method Value Component Layout Displays Regex Data Formatting Target Method Setup Map Scope Handle Fetch Returns Method Arrays Flow State Component Logic Setup Variables View Displays Handling Event Variables Component Map Action Method View Methods Mapping Fetch Rendering Check Render Handling Rendering Output Execute Object Handling Code View Flow Variable Method Event App Variables Outputs Values App Exec Results Results Value Layout Event App Flow Method Formats String Returns Code Component String Return Displays Display Functions Rendering Data Regex Check Execution Maps Call Components Setup Handle Prop Action Component Return Flow Array Code Fetch）
        if (!quoteMatches) {
          quoteMatches = quotesText.match(/> [\u201C""]([^\u201D""]+)[\u201D""]/g)
        }
        if (quoteMatches) {
          interview.quotes = quoteMatches
            .map(q => q.replace(/^> [\u201C""]|[\u201D""]$/g, '').trim())
            .filter(q => q)
        }
      }
      
      if (interview.name || interview.title) {
        result.interviews.push(interview)
      }
    })
    
    // Sinopse Questionário Base
    const summaryMatch = text.match(/### Síntese e opiniões chave da entrevista\n([\s\S]*?)$/)
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim()
    }
  } catch (e) {
    console.warn('Parse interview failed:', e)
  }
  
  return result
}

const parseQuickSearch = (text) => {
  const result = {
    query: '',
    count: 0,
    facts: [],
    edges: [],
    nodes: []
  }
  
  try {
    // Queries Box Extract Form Strings Values Return Methods Parser Call Logic Model Results Output Response Regex Searches Models Component Setup Vue Output Template Text Logic
    const queryMatch = text.match(/Output Execution Properties Mapping Logic Map Mapping State Displays Output Arrays Exec Format Method Methods Mapping Call View Components Methods Rendering Formatting View View Handling Execute Output Formatting Component Execution Arrays Run Prop Run Properties Handling String Results Handle Display Method Execute Returns Execute Result Result Rendering Process Return Properties Format Method Layout Process Output Execution Results Format Control Displays Results Event Method Flow Methods Event Object Action Result Component Execution Objects Array Result Check Return Exec Display Response Formatting String Object Function Check Call Format Mapping Setup Display Exec Method Output Pattern Regex Logic Action Results Formatting Results View Mapping Result Pattern Execute Objects Props Pattern Event Loop Action Results Result Process Setup Loop Setup Returns Target Array Objects Run Results Model Output Returns Returns Components Return Response Display:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Functions Regex Results Formatting Run Format Setup Formats Execute Variables State Rendering Variables Prop Handle Return Flow Setup Value Execution Action Render Code Components Target Formats Rendering Code Result Result Response Output Code Mapping Execution Formatting Flow Method Output Result Result Rendering Displays Code Function Control Process Code Mapping State Results Mapping Results Process Output Object Component Mapping Return Arrays Scope Results Code Result Exec Objects Target Data Flow Fetch Execution Scope Regex Target Outputs Run Run Control Formatting Render Render Pattern Output Rendering Render Output Values Mapping Flow Object Event Flow Response Value Flow Return Execute Arrays Execute Call Action Variables Displays Match Displays Loop Outputs Check Execution Run Layout Object Object Fetch Variables Event Component Call String Action Variables Outputs Returns Regex Execution Match Arrays Array Variables Call
    const countMatch = text.match(/Descoberto\s*(\d+)\s*Rows Iteration String Items Number Array List Object Values List Array Rendering Item Item Value Check Target Model App Iterate Number Loop Value Array Map Item Iteration View Run Methods Loop Components Update Loop Iterate Output Function Output Element Vue/)
    if (countMatch) result.count = parseInt(countMatch[1])
    
    // Fact Result Parsing Target Return Info Array Target Extract Response Call Run Execution Fetch Values Properties Model Format Value Objects Mapping Data Object Process Mapping Run Data Result Vue App Function String Array Property Results Function Regex Execution Output Property Logic Render Setup Info Vue Display Action App Method Process Array Info Model Array Execution Logic Map Returns Check Value Property Results Setup Regex Format Parse Check Data Structure Model Model Structure Values Code Variable Data Variable Methods App Values Output Text Control Object Render Format Control Result Object Data Return Info Value Components Properties Regex Call Execution Object Properties Regex Object Setup Method Run Value Result Code Model Fetch Flow Check Return Text Array Data Text Exec Output Process Fetch Run Model Model Output Objects Flow Setup Regex Array Setup Methods Event Code View Template Component Result Prop Component Return Logic Call Flow Object Handle Property - Retrieve Control Exec Fetch Response Event Prop View Method String Handling Layout Output Arrays Mapping Returns Exec Methods Display Check Variable Exec Property Setup Control Control Logic Variables Control Function Method Method Target Handling Action Mapping Check Array Array View Properties Array View Displays Objects Layout Setup Code Code Scope Target Layout Results Prop Scope Loop Display Control Call Pattern Fetch Displays Mapping Render Call Handling Outputs Exec Run Display Check Displays Results Methods Displays Functions Value Logic Function Mapping Execution Target Prop Control Scope Action Event Results Layout Action Variables Function Output String Event Props Properties Method Exec Value Method Event Output Outputs Objects Handle Handle Fetch Action Handling Result Displays Setup Mapping Prop Arrays Returns Variable Action Object Control Method Execution Scope Display Setup Exec Arrays Execute Setup
    const factsSection = text.match(/### Relation Facts Data Links DB ZEP Memory Context String Facts:\n([\s\S]*)$/)
    if (factsSection) {
      const lines = factsSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.facts = lines.map(l => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
    }
    
    // Component Function Logic Props Object Mapping Component Render Methods Formats Properties Match Component State Variable Fetch Target Props Layout Properties Flow Display Exec Arrays Methods Pattern Logic Fetch Exec Run Scope Model Model Component Outputs Check Event Run Code Run Displays Flow String State Handling Handling Variable View Action Displays Components Variables Object Response Displays Formatting Action Regex Props Returns View Handling Variable Formatting Target Method Outputs Handling App Fetch Functions Response Mapping Call Variables Handling Displays Outputs Props Component Map Array Variables Objects Arrays Render Prop Displays View Event Event Handling Formats Format Variable Components Fetch Objects Action Action Exec Values Run Variables Map String Data Execute Data Method Return Methods Function Response Return Match App Variables Loop Handling Arrays Pattern Output Variables Rendering Formatting Result Process Logic Mapping String）
    const edgesSection = text.match(/### Relation Type String Variable Name Key Name Keys Schema Object Type Properties Info Target Type Label Edges Link Value Check Graph Schema Structure Network Elements Array Source Targets Node Links Connections Info Data Fetch Display Components Scope Layout Variables Format Bind Object Structure Return Target Model Output Values Keys Loop Rendering List View Templates Props Array Values Text Property String Node Info Type Data Value Link Path Details Connections Relation List Name Types Links Object:\n([\s\S]*?)(?=\n###|$)/)
    if (edgesSection) {
      const lines = edgesSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.edges = lines.map(l => {
        const match = l.match(/^-\s*(.+?)\s*--\[(.+?)\]-->\s*(.+)$/)
        if (match) {
          return { source: match[1].trim(), relation: match[2].trim(), target: match[3].trim() }
        }
        return null
      }).filter(Boolean)
    }
    
    // Resgatar info de node no BD RAG）
    const nodesSection = text.match(/### Execute Exec Props Setup Formatting Logic Component Properties Method Output Event Handling Render Logic Action Fetch Check Logic Render Rendering Exec Component Formatting Map Values String Arrays Response Setup Result Result Methods Function Code Output Result Array Action Flow Variable Values View Code Mapping Returns Arrays Execute Values Display Mapping Map Array State Pattern Variable Check Control Match Mapping Flow Event Process Regex Output Scope Props Object Result Output Flow Object Loop Execute Return View Method Handle Handling Match Functions Pattern Setup Displays Outputs Array Process Display Event Values Component Handle Fetch Pattern Model Prop Run Layout Event Action Methods Code Methods Target Variables Array Displays Setup Arrays Objects Prop Render Output Action Execution Arrays Methods Display Scope Call Array Setup Prop Logic Run Object Component Values Results Component Flow Props Map Action Model Output:\n([\s\S]*?)(?=\n###|$)/)
    if (nodesSection) {
      const lines = nodesSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.nodes = lines.map(l => {
        const match = l.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        if (match) return { name: match[1].trim(), type: match[2].trim() }
        const simpleMatch = l.match(/^-\s*(.+)$/)
        if (simpleMatch) return { name: simpleMatch[1].trim(), type: '' }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse quick_search failed:', e)
  }
  
  return result
}

// ========== Sub Components ==========

// Insight Display Component - Enhanced with full data rendering (Interview-like style)
const InsightDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('facts') // 'facts', 'entities', 'relations', 'subqueries'
    const expandedFacts = ref(false)
    const expandedEntities = ref(false)
    const expandedRelations = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return `${(length / 1000).toFixed(1)}k chars`
      }
      return `${length} chars`
    }
    
    return () => h('div', { class: 'insight-display' }, [
      // Header Section - like interview header
      h('div', { class: 'insight-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, 'Deep Insight'),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.facts || props.result.facts.length),
              h('span', { class: 'stat-label' }, 'Facts')
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.entities || props.result.entities.length),
              h('span', { class: 'stat-label' }, 'Entities')
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.relationships || props.result.relations.length),
              h('span', { class: 'stat-label' }, 'Relations')
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-topic' }, props.result.query),
        props.result.simulationRequirement && h('div', { class: 'header-scenario' }, [
          h('span', { class: 'scenario-label' }, t('step4.scenarioLabel')),
          h('span', { class: 'scenario-text' }, props.result.simulationRequirement)
        ])
      ]),
      
      // Tab Navigation
      h('div', { class: 'insight-tabs' }, [
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'facts' }],
          onClick: () => { activeTab.value = 'facts' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabKeyFacts', { count: props.result.facts.length }))
        ]),
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'entities' }],
          onClick: () => { activeTab.value = 'entities' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabCoreEntities', { count: props.result.entities.length }))
        ]),
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'relations' }],
          onClick: () => { activeTab.value = 'relations' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabRelationChains', { count: props.result.relations.length }))
        ]),
        props.result.subQueries.length > 0 && h('button', {
          class: ['insight-tab', { active: activeTab.value === 'subqueries' }],
          onClick: () => { activeTab.value = 'subqueries' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabSubQueries', { count: props.result.subQueries.length }))
        ])
      ]),
      
      // Tab Content
      h('div', { class: 'insight-content' }, [
        // Facts Tab
        activeTab.value === 'facts' && props.result.facts.length > 0 && h('div', { class: 'facts-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelKeyFacts')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.facts.length }))
          ]),
          h('div', { class: 'facts-list' },
            (expandedFacts.value ? props.result.facts : props.result.facts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ),
          props.result.facts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedFacts.value = !expandedFacts.value }
          }, expandedFacts.value ? t('step4.collapse') : t('step4.expandAll', { count: props.result.facts.length }))
        ]),

        // Entities Tab
        activeTab.value === 'entities' && props.result.entities.length > 0 && h('div', { class: 'entities-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelCoreEntities')),
            h('span', { class: 'panel-count' }, t('step4.totalEntityCount', { count: props.result.entities.length }))
          ]),
          h('div', { class: 'entities-grid' },
            (expandedEntities.value ? props.result.entities : props.result.entities.slice(0, 12)).map((entity, i) => 
              h('div', { class: 'entity-tag', key: i, title: entity.summary || '' }, [
                h('span', { class: 'entity-name' }, entity.name),
                h('span', { class: 'entity-type' }, entity.type),
                entity.relatedFactsCount > 0 && h('span', { class: 'entity-fact-count' }, t('step4.factCount', { count: entity.relatedFactsCount }))
              ])
            )
          ),
          props.result.entities.length > 12 && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedEntities.value = !expandedEntities.value }
          }, expandedEntities.value ? t('step4.collapse') : t('step4.expandAllEntities', { count: props.result.entities.length }))
        ]),

        // Relations Tab
        activeTab.value === 'relations' && props.result.relations.length > 0 && h('div', { class: 'relations-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelRelationChains')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.relations.length }))
          ]),
          h('div', { class: 'relations-list' },
            (expandedRelations.value ? props.result.relations : props.result.relations.slice(0, INITIAL_SHOW_COUNT)).map((rel, i) => 
              h('div', { class: 'relation-item', key: i }, [
                h('span', { class: 'rel-source' }, rel.source),
                h('span', { class: 'rel-arrow' }, [
                  h('span', { class: 'rel-line' }),
                  h('span', { class: 'rel-label' }, rel.relation),
                  h('span', { class: 'rel-line' })
                ]),
                h('span', { class: 'rel-target' }, rel.target)
              ])
            )
          ),
          props.result.relations.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedRelations.value = !expandedRelations.value }
          }, expandedRelations.value ? t('step4.collapse') : t('step4.expandAll', { count: props.result.relations.length }))
        ]),

        // Sub-queries Tab
        activeTab.value === 'subqueries' && props.result.subQueries.length > 0 && h('div', { class: 'subqueries-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelSubQueries')),
            h('span', { class: 'panel-count' }, t('step4.totalEntityCount', { count: props.result.subQueries.length }))
          ]),
          h('div', { class: 'subqueries-list' },
            props.result.subQueries.map((sq, i) => 
              h('div', { class: 'subquery-item', key: i }, [
                h('span', { class: 'subquery-number' }, `Q${i + 1}`),
                h('div', { class: 'subquery-text' }, sq)
              ])
            )
          )
        ]),
        
        // Empty state
        activeTab.value === 'facts' && props.result.facts.length === 0 && h('div', { class: 'empty-state' }, t('step4.emptyKeyFacts')),
        activeTab.value === 'entities' && props.result.entities.length === 0 && h('div', { class: 'empty-state' }, t('step4.emptyCoreEntities')),
        activeTab.value === 'relations' && props.result.relations.length === 0 && h('div', { class: 'empty-state' }, t('step4.emptyRelationChains'))
      ])
    ])
  }
}

// Panorama Display Component - Enhanced with Active/Historical tabs
const PanoramaDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('active') // 'active', 'historical', 'entities'
    const expandedActive = ref(false)
    const expandedHistorical = ref(false)
    const expandedEntities = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return `${(length / 1000).toFixed(1)}k chars`
      }
      return `${length} chars`
    }
    
    return () => h('div', { class: 'panorama-display' }, [
      // Header Section
      h('div', { class: 'panorama-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, 'Panorama Search'),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.nodes),
              h('span', { class: 'stat-label' }, 'Nodes')
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.edges),
              h('span', { class: 'stat-label' }, 'Edges')
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-topic' }, props.result.query)
      ]),
      
      // Tab Navigation
      h('div', { class: 'panorama-tabs' }, [
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'active' }],
          onClick: () => { activeTab.value = 'active' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabActiveFacts', { count: props.result.activeFacts.length }))
        ]),
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'historical' }],
          onClick: () => { activeTab.value = 'historical' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabHistoricalFacts', { count: props.result.historicalFacts.length }))
        ]),
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'entities' }],
          onClick: () => { activeTab.value = 'entities' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabEntities', { count: props.result.entities.length }))
        ])
      ]),
      
      // Tab Content
      h('div', { class: 'panorama-content' }, [
        // Active Facts Tab
        activeTab.value === 'active' && h('div', { class: 'facts-panel active-facts' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelActiveFacts')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.activeFacts.length }))
          ]),
          props.result.activeFacts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedActive.value ? props.result.activeFacts : props.result.activeFacts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item active', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.emptyActiveFacts')),
          props.result.activeFacts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedActive.value = !expandedActive.value }
          }, expandedActive.value ? t('step4.collapse') : t('step4.expandAll', { count: props.result.activeFacts.length }))
        ]),
        
        // Historical Facts Tab
        activeTab.value === 'historical' && h('div', { class: 'facts-panel historical-facts' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelHistoricalFacts')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.historicalFacts.length }))
          ]),
          props.result.historicalFacts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedHistorical.value ? props.result.historicalFacts : props.result.historicalFacts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item historical', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, [
                  // Functions Response Displays Formats Functions Returns Handle Process Component Variable Code Check Arrays Layout Returns Setup Components Setup Setup Method Event Check Method Data Display Function Outputs Return String Setup Results Displays Variables Run Call Render Method Outputs Method String Process Logic Mapping Values Fetch Variables Method Methods Displays Fetch Returns Returns Setup Pattern Setup Methods Methods Method Format Results Arrays Render Method Flow Objects Output Check Variables Displays State Output String Loop Pattern String Fetch Displays Formatting Value Layout Mapping Map Setup Arrays Action Format Formats App Fetch Check View Logic Returns Execution Components Call Prop Setup Function Setup Methods Result Displays Match Objects Returns Outputs Displays Layout Displays Execution Map Target Returns Action Method Array Displays Results Flow Array Process Execution Event Handle Run Logic Displays Call Displays Outputs State Action String Format Logic Variable [time - time]
                  (() => {
                    const timeMatch = fact.match(/^\[(.+?)\]\s*(.*)$/)
                    if (timeMatch) {
                      return [
                        h('span', { class: 'fact-time' }, timeMatch[1]),
                        h('span', { class: 'fact-text' }, timeMatch[2])
                      ]
                    }
                    return h('span', { class: 'fact-text' }, fact)
                  })()
                ])
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.emptyHistoricalFacts')),
          props.result.historicalFacts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedHistorical.value = !expandedHistorical.value }
          }, expandedHistorical.value ? t('step4.collapse') : t('step4.expandAll', { count: props.result.historicalFacts.length }))
        ]),
        
        // Entities Tab
        activeTab.value === 'entities' && h('div', { class: 'entities-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelEntities')),
            h('span', { class: 'panel-count' }, t('step4.totalEntityCount', { count: props.result.entities.length }))
          ]),
          props.result.entities.length > 0 ? h('div', { class: 'entities-grid' },
            (expandedEntities.value ? props.result.entities : props.result.entities.slice(0, 8)).map((entity, i) => 
              h('div', { class: 'entity-tag', key: i }, [
                h('span', { class: 'entity-name' }, entity.name),
                entity.type && h('span', { class: 'entity-type' }, entity.type)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.emptyEntities')),
          props.result.entities.length > 8 && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedEntities.value = !expandedEntities.value }
          }, expandedEntities.value ? t('step4.collapse') : t('step4.expandAllEntities', { count: props.result.entities.length }))
        ])
      ])
    ])
  }
}

// Interview Display Component - Conversation Style (Q&A Format)
const InterviewDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return `${(length / 1000).toFixed(1)}k chars`
      }
      return `${length} chars`
    }
    
    // Clean quote text - remove leading list numbers to avoid double numbering
    const cleanQuoteText = (text) => {
      if (!text) return ''
      // Remove leading patterns like "1. ", "2. ", "1、", "（1）", "(1)" etc.
      return text.replace(/^\s*\d+[\.\、\)）]\s*/, '').trim()
    }
    
    const activeIndex = ref(0)
    const expandedAnswers = ref(new Set())
    // Para todas interrogativas-Reply Response Control Platforms State Data Setup Isolated Component State Var
    const platformTabs = reactive({}) // { 'agentIdx-qIdx': 'twitter' | 'reddit' }
    
    // Fetch Choice Box Control Var Setup Binding Method Data Access Model Object Properties Target Return Values String Enum Value Key Match
    const getPlatformTab = (agentIdx, qIdx) => {
      const key = `${agentIdx}-${qIdx}`
      return platformTabs[key] || 'twitter'
    }
    
    // Setup Networks Box Option Arrays Models Bound Sets
    const setPlatformTab = (agentIdx, qIdx, platform) => {
      const key = `${agentIdx}-${qIdx}`
      platformTabs[key] = platform
    }
    
    const toggleAnswer = (key) => {
      const newSet = new Set(expandedAnswers.value)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      expandedAnswers.value = newSet
    }
    
    const formatAnswer = (text, expanded) => {
      if (!text) return ''
      if (expanded || text.length <= 400) return text
      return text.substring(0, 400) + '...'
    }
    
    // Format Handling Returns Handling Logic Execution Rendering Output View Execution Arrays Regex Variables Setup String Return Display Flow Array Method Object Logic Display Arrays Values Variables Flow Component Object Model Flow Properties Results Flow Displays Action Data Props Scope Flow Layout Output Method Flow Components Output Call Results Object Array Setup Model Results Variable Component Execute Execute Result Loop Fetch Code Handle Result Return Arrays Value Mapping Arrays View Result Target Mapping Action String Event Object Map Execute Prop Mapping Code Output Response Mapping Mapping Render Setup Component Regex Flow Event Map Target Pattern Array Array Return Logic Variables Exec View Run Process Method Check Components Run Pattern Handling Target Execute Variables Code Handling Values Execution Code Handling Result Flow Display Layout Function Call Result Regex Displays Mapping Mapping Objects Outputs Execute Exec Array Run Flow Loop View Formatting Output Props Props View Handling Object Response Arrays Data Call Exec Flow Results Handling Return Handling Fetch Run Results Components Execution
    const isPlaceholderText = (text) => {
      if (!text) return true
      const t = text.trim()
      return t === '（Output Render Methods Displays Methods Mapping Methods Layout Run Handling Event Formats Returns Formats Returns Formats Render View Execute Handle Response Setup View Object Run View Mapping Methods Array Display Regex Run Functions Event Exec Arrays Code Mapping Loop Variables Output Target Run Execution Control Handling Variables Functions Format Method Prop Result Handle Render Format Run Run Handling Execution Action Display Fetch App Return Logic Execute Formatting Format Methods Component Display Methods Output Arrays Array Run Call Formats Values Control Returns Setup Format Code Return Control Map Run Component Prop Scope Call Results Call Outputs Displays Methods String Fetch Functions Methods Display Action Render Exec Output Exec Mapping Setup Formats Handling Objects Action Handle Returns Run Target Fetch Result Variables Variable Scope Exec Render Target Regex Action Target Loop Regex Objects Variables Layout Result Result Exec Target Array Object Array Run Model Execution String Format Execute Call Flow Render Array String Model Format View Output Output Handle Flow Output Data）' || t === '(Output Render Methods Displays Methods Mapping Methods Layout Run Handling Event Formats Returns Formats Returns Formats Render View Execute Handle Response Setup View Object Run View Mapping Methods Array Display Regex Run Functions Event Exec Arrays Code Mapping Loop Variables Output Target Run Execution Control Handling Variables Functions Format Method Prop Result Handle Render Format Run Run Handling Execution Action Display Fetch App Return Logic Execute Formatting Format Methods Component Display Methods Output Arrays Array Run Call Formats Values Control Returns Setup Format Code Return Control Map Run Component Prop Scope Call Results Call Outputs Displays Methods String Fetch Functions Methods Display Action Render Exec Output Exec Mapping Setup Formats Handling Objects Action Handle Returns Run Target Fetch Result Variables Variable Scope Exec Render Target Regex Action Target Loop Regex Objects Variables Layout Result Result Exec Target Array Object Array Run Model Execution String Format Execute Call Flow Render Array String Model Format View Output Output Handle Flow Output Data)' || t === '[Silêncio]'
    }

    // Displays Map Handle Action Display Fetch Displays Methods Variables Match Action Run Map Return Call Pattern Event Scope Logic Handling Methods Outputs Functions Object Loop Properties Outputs Model Returns Value Maps Logic Run Render Event Logic Mapping Return Regex Maps Output Values Data Display Functions Fetch Display App Handling Execute Action Run Fetch Setup Layout Outputs Returns Format Component Return Values Target Execute Map Flow Return Output Execution Value App Format Component Arrays Format Objects Results Exec Display Object Values Displays Objects Mapping Arrays Action Handle Method Execution Setup Outputs Method Results Setup Output Objects View Event Functions Method String Function Mapping Action Target Arrays Maps Formats Result Display Return Result Returns Component Action Components Format Value Response Logic Scope Displays Handling Execution String Properties Method Logic Variables Logic Display Event Mapping Logic Call String Prop Output Event Component Handling Results Return Object View Output Result Formats Function State Props Variable Format Functions Return Mapping Methods Return Return Handling Run Control Properties Formats Functions Result Execute Return Execute Functions Output Props
    const splitAnswerByQuestions = (answerText, questionCount) => {
      if (!answerText || questionCount <= 0) return [answerText]
      if (isPlaceholderText(answerText)) return ['']

      // Regex Dual Suporte Vars List Numbers：
      // 1. "DesafioX：" Verso "DesafioX:" （Formatos Locais PT）
      // 2. "1. " Verso "\n1. " （Digits+Dots Old Format Legacy Logic Check Regex Models Process Support）
      let matches = []
      let match

      // Action Array Flow Mapping Data Object Value Output Variables Match Array App Layout Method Value Returns Render Execute Rendering Methods Execution Display Regex Code View Prop Handling Format Action Check Display Result Variables Mapping Properties Formats Handling Execution Component Execute Arrays Data Return View Values Logic String Formats Handling State App Result Fetch Exec Action Code Methods Value Model Data Format Display Result Scope Scope Output Code Returns Function Value Formatting Target Output Mapping Action Values Formats Call Rendering Properties Call Methods Match Fetch Regex Array Process Regex Handle Data Response Execution Handling Formatting Mapping Fetch Output Process Arrays Prop Fetch Fetch String Variable Logic Results Pattern Method Props Object Results Function Method Flow Prop Render Results App Call Components Control Fetch Run Handling Display Render Return Check Scope Map Setup Returns Output Run Components Run Displays Render Layout Logic Check Array Match Object Display Display Logic Logic Methods Properties Setup Prop "DesafioX：" 格式
      const cnPattern = /(?:^|[\r\n]+)Desafio(\d+)[：:]\s*/g
      while ((match = cnPattern.exec(answerText)) !== null) {
        matches.push({
          num: parseInt(match[1]),
          index: match.index,
          fullMatch: match[0]
        })
      }

      // Fallback para mismatch "Digits." 格式
      if (matches.length === 0) {
        const numPattern = /(?:^|[\r\n]+)(\d+)\.\s+/g
        while ((match = numPattern.exec(answerText)) !== null) {
          matches.push({
            num: parseInt(match[1]),
            index: match.index,
            fullMatch: match[0]
          })
        }
      }

      // Variables Object Result Rendering Object Methods Formatting Method Exec Output View Event Exec Prop Scope Call Properties Handling Render Logic Return Display Properties State Render Process Target Display Methods String Variables Arrays Outputs Action Arrays Fetch Execute Map Result Check Setup Execute Handling Map Function Run Results Object Return Object Action Run Display Event Method Properties Method Loop Match Arrays Action Action Display Object Methods Array Result Object Components Execution Variable Setup Action Run Call Objects Pattern Props Run Returns Run Properties Variable Execution Results View Object Component Methods Output Layout Action Data Method Output Prop Output Flow Variable Run Pattern Data Event Handling Props Exec Match Result String Methods Map Objects Array Loop Check Control
      if (matches.length <= 1) {
        const cleaned = answerText
          .replace(/^Desafio\d+[：:]\s*/, '')
          .replace(/^\d+\.\s+/, '')
          .trim()
        return [cleaned || answerText]
      }

      // Value Function Display Object Displays Props Action Methods Event Render Method Action Formats Execution Logic Result View Component Mapping Object Arrays Rendering Value Fetch Process Arrays Run Return Render Mapping Handling Format Fetch Formatting Properties Output Logic State Arrays Outputs Render Formats Function Arrays Mapping Handling Returns Call Returns Execute Run Call Exec Loop Properties Setup Layout Control Exec Fetch Prop Event Formats Logic Exec Response Mapping Method Output State Function Output Properties State Variable Code Fetch Handling Exec Handling Format Prop Output Components Check Map Fetch Output Flow Rendering Component Display Handle Returns Component Layout Handle Process Code Formats Array Flow Event Rendering Array Formats Methods Output Returns Fetch Variable Control Setup Handling Object Component Result Render Mapping String Handle Setup Components Map Mapping Exec Handle Prop Formatting Rendering String Loop Run Scope Call Fetch Methods Flow State Displays Value Scope Arrays Fetch Action Response Arrays State Map Fetch Action Components Event Prop Value Flow Handling Execution Format Logic Value Formatting Exec Loop Component Format Method Logic Scope Variables Process String Returns Method String
      const parts = []
      for (let i = 0; i < matches.length; i++) {
        const current = matches[i]
        const next = matches[i + 1]

        const startIdx = current.index + current.fullMatch.length
        const endIdx = next ? next.index : answerText.length

        let part = answerText.substring(startIdx, endIdx).trim()
        part = part.replace(/[\r\n]+$/, '').trim()
        parts.push(part)
      }

      if (parts.length > 0 && parts.some(p => p)) {
        return parts
      }

      return [answerText]
    }
    
    // Capturar o gabarito
    const getAnswerForQuestion = (interview, qIdx, platform) => {
      const answer = platform === 'twitter' ? interview.twitterAnswer : (interview.redditAnswer || interview.twitterAnswer)
      if (!answer || isPlaceholderText(answer)) return answer || ''

      const questionCount = interview.questions?.length || 1
      const answers = splitAnswerByQuestions(answer, questionCount)

      // Format Mapping Display Pattern Component Run Result Render Format Exec Execute Model Call Displays Display State Returns View Array Event Maps Mapping Return Action Returns Object Response Props Formatting Exec Displays Control App Arrays Run Variable Setup Maps Map Result Action Execute Method Object Returns Rendering View Value Component Layout Displays Flow Render Variable Map Displays Format Code Loop Results Map Results Display Map Action Method Value Returns Output Return Setup Object Layout Returns Execution Display Run App Execute Methods Match Output Setup Regex Display Return Rendering Values Props Logic Variables Value Exec Exec String Output Rendering Mapping Functions Values Result Arrays Action Values Variables Method App Object Values Format Variables Data Layout Match Properties Flow Run Handling Code Object View Scope Data Object Loop Action Object Arrays Map Format Value Formats Format Result Result Array Variables Target State
      if (answers.length > 1 && qIdx < answers.length) {
        return answers[qIdx] || ''
      }

      // Fail Split Exception Logic Model Output Fallback Handle Catch Values Regex Miss Structure Unhandled Break Exception Array Split Logic String Parsing Code Method Functions Flow Run Output Setup Values Vars Error Debug Variables Values Set Output Return Control Empty Missing Broken Error Data Vue Action Target Return Result Flow Response Call Exec Results Exception Code Control Block Run Process Check Next Handle Run Call Logic Return Process Result Flow Next Check Results App Target Loop Error Output Data
      return qIdx === 0 ? answer : ''
    }
    
    // Format Pattern Return Output Target Return Control Values Format Response Handling Control Output Response Setup Run Exec Control Map Function Display Fetch Regex Object App Returns Mapping Display Format Execute Value Data Values Displays Output Variable Exec Output Code Flow Return Format Layout Prop Logic Check Map Object Formats Check Arrays Execute Component Result Render Outputs Map Target Formats Object Result Variables Formatting Render Rendering Arrays Functions Model Control Execution Arrays View Setup Handling Event Fetch Layout Response Result Run Result Data Event Regex Formats Flow Result Object Method Mapping Flow Call Component Control Components Scope Function Variables Flow Arrays Model Handling Array Functions Response Result Match View Rendering Flow Event Match Execute Check Layout Check Handle Function Exec Check Setup Model Handling Arrays Fetch Execution Displays Setup Target Object View Pattern Formatting String Logic Handling Fetch Method Call Loop Functions Layout Code Model Outputs String Fetch Call Response Arrays Function Logic Components Control Flow Output String Display Method）
    const hasMultiplePlatforms = (interview, qIdx) => {
      if (!interview.twitterAnswer || !interview.redditAnswer) return false
      const twitterAnswer = getAnswerForQuestion(interview, qIdx, 'twitter')
      const redditAnswer = getAnswerForQuestion(interview, qIdx, 'reddit')
      // Duas redes informaram respostas opostas
      return !isPlaceholderText(twitterAnswer) && !isPlaceholderText(redditAnswer) && twitterAnswer !== redditAnswer
    }
    
    return () => h('div', { class: 'interview-display' }, [
      // Header Section
      h('div', { class: 'interview-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, 'Agent Interview'),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.successCount || props.result.interviews.length),
              h('span', { class: 'stat-label' }, 'Interviewed')
            ]),
            props.result.totalCount > 0 && h('span', { class: 'stat-divider' }, '/'),
            props.result.totalCount > 0 && h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.totalCount),
              h('span', { class: 'stat-label' }, 'Total')
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.topic && h('div', { class: 'header-topic' }, props.result.topic)
      ]),
      
      // Agent Selector Tabs
      props.result.interviews.length > 0 && h('div', { class: 'agent-tabs' }, 
        props.result.interviews.map((interview, i) => h('button', {
          class: ['agent-tab', { active: activeIndex.value === i }],
          key: i,
          onClick: () => { activeIndex.value = i }
        }, [
          h('span', { class: 'tab-avatar' }, interview.name ? interview.name.charAt(0) : (i + 1)),
          h('span', { class: 'tab-name' }, interview.title || interview.name || `Agent ${i + 1}`)
        ]))
      ),
      
      // Active Interview Detail
      props.result.interviews.length > 0 && h('div', { class: 'interview-detail' }, [
        // Agent Profile Card
        h('div', { class: 'agent-profile' }, [
          h('div', { class: 'profile-avatar' }, props.result.interviews[activeIndex.value]?.name?.charAt(0) || 'A'),
          h('div', { class: 'profile-info' }, [
            h('div', { class: 'profile-name' }, props.result.interviews[activeIndex.value]?.name || 'Agent'),
            h('div', { class: 'profile-role' }, props.result.interviews[activeIndex.value]?.role || ''),
            props.result.interviews[activeIndex.value]?.bio && h('div', { class: 'profile-bio' }, props.result.interviews[activeIndex.value].bio)
          ])
        ]),
        
        // Selection Reason - Fundamentar a decisão
        props.result.interviews[activeIndex.value]?.selectionReason && h('div', { class: 'selection-reason' }, [
          h('div', { class: 'reason-label' }, 'Fundamentar a decisão'),
          h('div', { class: 'reason-content' }, props.result.interviews[activeIndex.value].selectionReason)
        ]),
        
        // Q&A Conversation Thread - Q And A Pattern Regex Pattern Match Run Flow Call Function Response Values Component View Scope Render Value Components Props Template Data Match Process Call Response Run Action Event Method Process Values Display Format Run App Variable Event Variables Format Regex Pattern Execution Results Control Action Loop Render Output Scope Return Process Function Action Values Display Format Flow Method Scope Mapping Code Layout Render Run Result Control Pattern Execute Handle Event Values Component Data Action Array Call Output Setup Regex Match Output State Pattern Mapping Render Result Run Action Array Pattern Flow Execute Event Handling Loop Execution Target Control Map Process Rendering Results Control Handling Format Returns Flow Event Handling Components Match Check Regex Output DOM Run Execute Rendering Values Layout Response Call Execution Pattern Output View Layout Event Handle View Returns Control Call Regex Formats Array DOM Model
        h('div', { class: 'qa-thread' }, 
          (props.result.interviews[activeIndex.value]?.questions?.length > 0 
            ? props.result.interviews[activeIndex.value].questions 
            : [props.result.interviews[activeIndex.value]?.question || 'No question available']
          ).map((question, qIdx) => {
            const interview = props.result.interviews[activeIndex.value]
            const currentPlatform = getPlatformTab(activeIndex.value, qIdx)
            const answerText = getAnswerForQuestion(interview, qIdx, currentPlatform)
            const hasDualPlatform = hasMultiplePlatforms(interview, qIdx)
            const expandKey = `${activeIndex.value}-${qIdx}`
            const isExpanded = expandedAnswers.value.has(expandKey)
            const isPlaceholder = isPlaceholderText(answerText)

            return h('div', { class: 'qa-pair', key: qIdx }, [
              // Question Block
              h('div', { class: 'qa-question' }, [
                h('div', { class: 'qa-badge q-badge' }, `Q${qIdx + 1}`),
                h('div', { class: 'qa-content' }, [
                  h('div', { class: 'qa-sender' }, 'Interviewer'),
                  h('div', { class: 'qa-text' }, question)
                ])
              ]),

              // Answer Block
              answerText && h('div', { class: ['qa-answer', { 'answer-placeholder': isPlaceholder }] }, [
                h('div', { class: 'qa-badge a-badge' }, `A${qIdx + 1}`),
                h('div', { class: 'qa-content' }, [
                  h('div', { class: 'qa-answer-header' }, [
                    h('div', { class: 'qa-sender' }, interview?.name || 'Agent'),
                    // Action Output Logic Display Call Exec Call Action Displays Scope Value Values Result Scope Arrays Scope Scope Target Methods Method Output Action Handling Code Fetch Value Target Variables Components Layout Target Execution Handle Methods App Object Formatting Objects State Results Action Setup Display Code Props Formats Event Map Mapping Code Logic Fetch Handling Run Output Execution Object Map Return Run Returns Call Event Fetch Flow Returns Formats Response String Regex Event Model Functions Loop Model Display Execution Mapping Arrays Execute Action Arrays Fetch Scope Map Run Object Setup Flow Pattern Match Flow String Fetch Flow Returns Code Control Flow）
                    hasDualPlatform && h('div', { class: 'platform-switch' }, [
                      h('button', {
                        class: ['platform-btn', { active: currentPlatform === 'twitter' }],
                        onClick: (e) => { e.stopPropagation(); setPlatformTab(activeIndex.value, qIdx, 'twitter') }
                      }, [
                        h('svg', { class: 'platform-icon', viewBox: '0 0 24 24', width: 12, height: 12, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                          h('circle', { cx: '12', cy: '12', r: '10' }),
                          h('line', { x1: '2', y1: '12', x2: '22', y2: '12' }),
                          h('path', { d: 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' })
                        ]),
                        h('span', {}, t('step4.world1'))
                      ]),
                      h('button', {
                        class: ['platform-btn', { active: currentPlatform === 'reddit' }],
                        onClick: (e) => { e.stopPropagation(); setPlatformTab(activeIndex.value, qIdx, 'reddit') }
                      }, [
                        h('svg', { class: 'platform-icon', viewBox: '0 0 24 24', width: 12, height: 12, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                          h('path', { d: 'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z' })
                        ]),
                        h('span', {}, t('step4.world2'))
                      ])
                    ])
                  ]),
                  h('div', {
                    class: ['qa-text', 'answer-text', { 'placeholder-text': isPlaceholder }],
                    innerHTML: isPlaceholder
                      ? answerText
                      : formatAnswer(answerText, isExpanded)
                          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br>')
                  }),
                  // Expand/Collapse Button（Method State State Event Props Logic Setup Returns Output Match Props Result Result Setup Component Arrays Fetch Returns Result Flow Process Action Render Props Model Action Output Component Variables Formatting Action Array Component Event Return Run Fetch Execution Variables Method Component Return Execution Returns Object Execution Component Code Loop Results Target Mapping Exec Displays Result Object Flow Object Returns Result Rendering View String Formatting Map Action Mapping Outputs Formats Outputs Returns Objects View Outputs Handling Array Arrays Flow Fetch Array Methods Code Handle Handling Returns Props Mapping Arrays Props Component Control Run Logic Setup Result State Map Pattern Regex String Process Logic Call Layout Formats Formats Loop Logic Event Fetch App Execute Map Result Object Array Map Data Object Data Arrays Check Event Components Displays View Output Formats Execute Flow Mapping Scope Formatting Execution Fetch Map Event Functions Response Results Call Result Flow Results View Function Action Handling Execution Format Fetch Target Objects Execution Scope Returns Layout Prop Process Object Arrays Component Exec Flow Scope Props Variables Formats Props Setup Component Code Exec View Mapping Loop Output Event Fetch Exec Map Prop View Format Event Handle Display Variable Map Result Output Functions Setup Mapping String）
                  !isPlaceholder && answerText.length > 400 && h('button', {
                    class: 'expand-answer-btn',
                    onClick: () => toggleAnswer(expandKey)
                  }, isExpanded ? 'Show Less' : 'Show More')
                ])
              ])
            ])
          })
        ),
        
        // Key Quotes Section
        props.result.interviews[activeIndex.value]?.quotes?.length > 0 && h('div', { class: 'quotes-section' }, [
          h('div', { class: 'quotes-header' }, 'Key Quotes'),
          h('div', { class: 'quotes-list' },
            props.result.interviews[activeIndex.value].quotes.slice(0, 3).map((quote, qi) => {
              const cleanedQuote = cleanQuoteText(quote)
              const displayQuote = cleanedQuote.length > 200 ? cleanedQuote.substring(0, 200) + '...' : cleanedQuote
              return h('blockquote', { 
                key: qi, 
                class: 'quote-item',
                innerHTML: renderMarkdown(displayQuote)
              })
            })
          )
        ])
      ]),

      // Summary Section (Collapsible)
      props.result.summary && h('div', { class: 'summary-section' }, [
        h('div', { class: 'summary-header' }, 'Interview Summary'),
        h('div', { 
          class: 'summary-content',
          innerHTML: renderMarkdown(props.result.summary.length > 500 ? props.result.summary.substring(0, 500) + '...' : props.result.summary)
        })
      ])
    ])
  }
}

// Quick Search Display Component - Enhanced with full data rendering
const QuickSearchDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('facts') // 'facts', 'edges', 'nodes'
    const expandedFacts = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Check if there are edges or nodes to show tabs
    const hasEdges = computed(() => props.result.edges && props.result.edges.length > 0)
    const hasNodes = computed(() => props.result.nodes && props.result.nodes.length > 0)
    const showTabs = computed(() => hasEdges.value || hasNodes.value)
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return `${(length / 1000).toFixed(1)}k chars`
      }
      return `${length} chars`
    }
    
    return () => h('div', { class: 'quick-search-display' }, [
      // Header Section
      h('div', { class: 'quicksearch-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, 'Quick Search'),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.count || props.result.facts.length),
              h('span', { class: 'stat-label' }, 'Results')
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-query' }, [
          h('span', { class: 'query-label' }, t('step4.searchLabel')),
          h('span', { class: 'query-text' }, props.result.query)
        ])
      ]),
      
      // Tab Navigation (only show if there are edges or nodes)
      showTabs.value && h('div', { class: 'quicksearch-tabs' }, [
        h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'facts' }],
          onClick: () => { activeTab.value = 'facts' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabFacts', { count: props.result.facts.length }))
        ]),
        hasEdges.value && h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'edges' }],
          onClick: () => { activeTab.value = 'edges' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabEdges', { count: props.result.edges.length }))
        ]),
        hasNodes.value && h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'nodes' }],
          onClick: () => { activeTab.value = 'nodes' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.tabNodes', { count: props.result.nodes.length }))
        ])
      ]),
      
      // Content Area
      h('div', { class: ['quicksearch-content', { 'no-tabs': !showTabs.value }] }, [
        // Facts (always show if no tabs, or when facts tab is active)
        ((!showTabs.value) || activeTab.value === 'facts') && h('div', { class: 'facts-panel' }, [
          !showTabs.value && h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelSearchResults')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.facts.length }))
          ]),
          props.result.facts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedFacts.value ? props.result.facts : props.result.facts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.emptySearchResults')),
          props.result.facts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedFacts.value = !expandedFacts.value }
          }, expandedFacts.value ? t('step4.collapse') : t('step4.expandAll', { count: props.result.facts.length }))
        ]),
        
        // Edges Tab
        activeTab.value === 'edges' && hasEdges.value && h('div', { class: 'edges-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelRelatedEdges')),
            h('span', { class: 'panel-count' }, t('step4.totalCount', { count: props.result.edges.length }))
          ]),
          h('div', { class: 'edges-list' },
            props.result.edges.map((edge, i) => 
              h('div', { class: 'edge-item', key: i }, [
                h('span', { class: 'edge-source' }, edge.source),
                h('span', { class: 'edge-arrow' }, [
                  h('span', { class: 'edge-line' }),
                  h('span', { class: 'edge-label' }, edge.relation),
                  h('span', { class: 'edge-line' })
                ]),
                h('span', { class: 'edge-target' }, edge.target)
              ])
            )
          )
        ]),
        
        // Nodes Tab
        activeTab.value === 'nodes' && hasNodes.value && h('div', { class: 'nodes-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.panelRelatedNodes')),
            h('span', { class: 'panel-count' }, t('step4.totalEntityCount', { count: props.result.nodes.length }))
          ]),
          h('div', { class: 'nodes-grid' },
            props.result.nodes.map((node, i) => 
              h('div', { class: 'node-tag', key: i }, [
                h('span', { class: 'node-name' }, node.name),
                node.type && h('span', { class: 'node-type' }, node.type)
              ])
            )
          )
        ])
      ])
    ])
  }
}

// Computed
const statusClass = computed(() => {
  if (isComplete.value) return 'completed'
  if (agentLogs.value.length > 0) return 'processing'
  return 'pending'
})

const statusText = computed(() => {
  if (isComplete.value) return 'Completed'
  if (agentLogs.value.length > 0) return 'Generating...'
  return 'Waiting'
})

const totalSections = computed(() => {
  return reportOutline.value?.sections?.length || 0
})

const completedSections = computed(() => {
  return Object.keys(generatedSections.value).length
})

const progressPercent = computed(() => {
  if (totalSections.value === 0) return 0
  return Math.round((completedSections.value / totalSections.value) * 100)
})

const totalToolCalls = computed(() => {
  return agentLogs.value.filter(l => l.action === 'tool_call').length
})

const formatElapsedTime = computed(() => {
  if (!startTime.value) return '0s'
  const lastLog = agentLogs.value[agentLogs.value.length - 1]
  const elapsed = lastLog?.elapsed_seconds || 0
  if (elapsed < 60) return `${Math.round(elapsed)}s`
  const mins = Math.floor(elapsed / 60)
  const secs = Math.round(elapsed % 60)
  return `${mins}m ${secs}s`
})

const displayLogs = computed(() => {
  return agentLogs.value
})

// Workflow steps overview (status-based, no nested cards)
const activeSectionIndex = computed(() => {
  if (isComplete.value) return null
  if (currentSectionIndex.value) return currentSectionIndex.value
  if (totalSections.value > 0 && completedSections.value < totalSections.value) return completedSections.value + 1
  return null
})

const isPlanningDone = computed(() => {
  return !!reportOutline.value?.sections?.length || agentLogs.value.some(l => l.action === 'planning_complete')
})

const isPlanningStarted = computed(() => {
  return agentLogs.value.some(l => l.action === 'planning_start' || l.action === 'report_start')
})

const isFinalizing = computed(() => {
  return !isComplete.value && isPlanningDone.value && totalSections.value > 0 && completedSections.value >= totalSections.value
})

// Passo atual topo indexer）
const activeStep = computed(() => {
  const steps = workflowSteps.value
  // Get Step Status
  const active = steps.find(s => s.status === 'active')
  if (active) return active
  
  // If Check List Arrays Fallbacks Values
  const doneSteps = steps.filter(s => s.status === 'done')
  if (doneSteps.length > 0) return doneSteps[doneSteps.length - 1]
  
  // Fallback Step Value Zero Returns First Default Status Setup Start Flow Target Process Checks State Logic Return Fallback Methods Components Props Pass Parent Child Layout Control Setup
  return steps[0] || { noLabel: '--', title: 'Wait Prop Object Layout Execute Result State Rendering Returns Execution Fetch Mapping App Format Target Method Regex Method Results Logic Action Arrays Event Array Formats Function Event Run Properties Prop Flow View Fetch Scope Functions Results Components Event Call Format Object Map Functions Variables Output Target Displays Outputs Mapping Object Exec Loop Mapping Methods Array Results Components Format Handling Results Properties Execute Return Method Value Event Values Object Returns Logic Rendering Layout Action Check Scope Logic Setup Execute Arrays Methods Value Object Flow Model Call Variables Mapping Format Arrays Map Execute Mapping Mapping Execute Execution Response Data Arrays Action Formatting Fetch Flow Return Formats Scope', status: 'todo', meta: '' }
})

const workflowSteps = computed(() => {
  const steps = []

  // Planning / Outline
  const planningStatus = isPlanningDone.value ? 'done' : (isPlanningStarted.value ? 'active' : 'todo')
  steps.push({
    key: 'planning',
    noLabel: 'PL',
    title: 'Planning / Outline',
    status: planningStatus,
    meta: planningStatus === 'active' ? 'IN PROGRESS' : ''
  })

  // Sections (if outline exists)
  const sections = reportOutline.value?.sections || []
  sections.forEach((section, i) => {
    const idx = i + 1
    const status = (isComplete.value || !!generatedSections.value[idx])
      ? 'done'
      : (activeSectionIndex.value === idx ? 'active' : 'todo')

    steps.push({
      key: `section-${idx}`,
      noLabel: String(idx).padStart(2, '0'),
      title: section.title,
      status,
      meta: status === 'active' ? 'IN PROGRESS' : ''
    })
  })

  // Complete
  const completeStatus = isComplete.value ? 'done' : (isFinalizing.value ? 'active' : 'todo')
  steps.push({
    key: 'complete',
    noLabel: 'OK',
    title: 'Complete',
    status: completeStatus,
    meta: completeStatus === 'active' ? 'FINALIZING' : ''
  })

  return steps
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

const isSectionCompleted = (sectionIndex) => {
  return !!generatedSections.value[sectionIndex]
}

const DD_SECTIONS = {
  tese: ['tese', 'thesis', 'argument'],
  evidencias: ['evidências', 'evidencias', 'evidence', 'proofs'],
  fragilidades: ['fragilidades', 'fragilities', 'weaknesses', 'risks'],
  premissas: ['premissas', 'premises', 'assumptions'],
  cenarios: ['cenários', 'cenarios', 'scenarios', 'outcomes']
}

const isDueDiligenceSection = (title, type) => {
  if (!title || !type) return false
  const lower = title.toLowerCase()
  return DD_SECTIONS[type]?.some(k => lower.includes(k)) ?? false
}

const getDDSectionLabel = (title) => {
  if (isDueDiligenceSection(title, 'tese')) return 'Tese'
  if (isDueDiligenceSection(title, 'evidencias')) return 'Evidências'
  if (isDueDiligenceSection(title, 'fragilidades')) return 'Fragilidades'
  if (isDueDiligenceSection(title, 'premissas')) return 'Premissas'
  if (isDueDiligenceSection(title, 'cenarios')) return 'Cenários'
  return ''
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    })
  } catch {
    return ''
  }
}

const formatParams = (params) => {
  if (!params) return ''
  try {
    return JSON.stringify(params, null, 2)
  } catch {
    return String(params)
  }
}

const formatResultSize = (length) => {
  if (!length) return ''
  if (length < 1000) return `${length} chars`
  return `${(length / 1000).toFixed(1)}k chars`
}

const truncateText = (text, maxLen) => {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.substring(0, maxLen) + '...'
}

// Parse markdown tables into HTML
const parseMarkdownTables = (content) => {
  // Match table blocks: header row + separator + data rows
  const tableRegex = /^(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)/gm
  
  return content.replace(tableRegex, (match) => {
    const lines = match.trim().split('\n').filter(l => l.trim())
    if (lines.length < 2) return match
    
    // Check if second line is a separator
    const separatorLine = lines[1].trim()
    if (!/^\|[\s\-:|]+\|$/.test(separatorLine)) return match
    
    // Parse header
    const headerCells = lines[0].split('|').slice(1, -1).map(c => c.trim())
    // Parse rows (skip header and separator)
    const rows = lines.slice(2).map(line => {
      return line.split('|').slice(1, -1).map(c => c.trim())
    })
    
    let html = '<table class="report-table"><thead><tr>'
    headerCells.forEach(cell => {
      html += `<th>${cell}</th>`
    })
    html += '</tr></thead><tbody>'
    
    rows.forEach(row => {
      html += '<tr>'
      row.forEach(cell => {
        html += `<td>${cell}</td>`
      })
      html += '</tr>'
    })
    html += '</tbody></table>'
    
    return html
  })
}

// Parse data source tags like [📊 realizado] into styled spans
const parseDataSourceTags = (content) => {
  return content
    .replace(/\[📊\s*realizado\]/g, '<span class="source-tag source-realizado">📊 realizado</span>')
    .replace(/\[🔮\s*hip[oó]tese\]/g, '<span class="source-tag source-projecao">🔮 hipótese</span>')
    .replace(/\[📈\s*consenso\]/g, '<span class="source-tag source-consenso">📈 consenso</span>')
    .replace(/\[⚠️\s*simula[cç][aã]o\]/g, '<span class="source-tag source-simulacao">⚠️ simulação</span>')
}

const renderMarkdown = (content) => {
  if (!content) return ''
  
  // Parse tables first (before other transformations)
  let processedContent = parseMarkdownTables(content)
  
  // Parse data source tags
  processedContent = parseDataSourceTags(processedContent)
  
  // Remove first H2 (used as section title)
  processedContent = processedContent.replace(/^##\s+.+\n+/, '')
  
  // Format Syntax Highlight Block Parser Code Execute Render Pre Tags Content View DOM Flow String Replace Value CSS Styles Control Handle Run Formats Target Setup Layout Regex Component Return Render String Check Replace Methods Output Parse Markdown Transform Data Control Value DOM Check Action Vue App Logic Vue View Components View Component Output Handle Run Check Formats Control Target Result Flow DOM Method Return Format Execution Component Vue Call Execute Return Setup Code Execution Vue String Values Replace Target Array Flow Render Setup Execution Flow String Replace Code Results Components Call Method App Layout Format Component Output Format Render Output App Logic Methods Flow Render Syntax Handle Transform Parse View Call Target String Methods Code Setup Replace Array
  let html = processedContent.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  
  // Outputs Variables Output Display Returns Props Code Execute Object Results Variable Render Match Result Displays Results Pattern Result Return Action App Returns Run Scope Check Results Mapping Layout Array Output Return Execution Methods View Displays Maps Results Component Action Flow Method Action Logic Method Run State Loop Exec Fetch Target Arrays Mapping Values Functions Method String Method Call Format Mapping Object Outputs Action Variable Data Outputs Value Control Handling Data Action Event String Map Execute View Call Formats Flow Layout Flow Event Formats Output Result Logic Outputs Mapping Render Array Exec Results Array Target Execute Check Displays Outputs Handle Methods Flow Fetch Props Output Value Setup Handling Methods Call Arrays View Props Execution Data Check Fetch Results Output Result Output Results Component Formats
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // Formata topicos with IDs for outline navigation
  const slugify = (text) => text.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-').substring(0, 50)
  html = html.replace(/^#### (.+)$/gm, (_, t) => `<h5 class="md-h5" id="h5-${slugify(t)}">${t}</h5>`)
  html = html.replace(/^### (.+)$/gm, (_, t) => `<h4 class="md-h4" id="h4-${slugify(t)}">${t}</h4>`)
  html = html.replace(/^## (.+)$/gm, (_, t) => `<h3 class="md-h3" id="h3-${slugify(t)}">${t}</h3>`)
  html = html.replace(/^# (.+)$/gm, (_, t) => `<h2 class="md-h2" id="h2-${slugify(t)}">${t}</h2>`)
  
  // 处理Referência PointerChunks Format Results Array Handling Data Target Fetch Response Output View Run Exec Flow Component Return Render Variable Object Scope Values Execution Exec Result Function Flow View Render Execute Method Formatting Call Output Exec Prop Variable Results Formatting Handling Value Model Target Data Display Event Fetch Flow Call Mapping Response Mapping Fetch Array DOM Model Execution Fetch Variable Mapping Component Run Flow Output Arrays Map Loop Layout Handle Response Execute Component Handling Output DOM Value Data Object Result Result Variable Event Call Mapping Format Array Arrays Method Setup Variables Exec Output Rendering Execute Output Variables Exec Components Layout Handling Array Match Display Flow Control Function Loop Mapping Action Match Exec Event Output Response View Mapping Formatting Array Render Scope Array Call Data Event Mapping Flow Result Pattern Output Execution Function Pattern Array Function Result Method String Result Format Returns Map Layout
  html = html.replace(/^> (.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')
  
  // 处理Listas Arrays - 支持子Listas Arrays
  html = html.replace(/^(\s*)- (.+)$/gm, (match, indent, text) => {
    const level = Math.floor(indent.length / 2)
    return `<li class="md-li" data-level="${level}">${text}</li>`
  })
  html = html.replace(/^(\s*)(\d+)\. (.+)$/gm, (match, indent, num, text) => {
    const level = Math.floor(indent.length / 2)
    return `<li class="md-oli" data-level="${level}">${text}</li>`
  })

  // 包装无序Listas Arrays
  html = html.replace(/(<li class="md-li"[^>]*>.*?<\/li>\s*)+/g, '<ul class="md-ul">$&</ul>')
  // 包装有序Listas Arrays
  html = html.replace(/(<li class="md-oli"[^>]*>.*?<\/li>\s*)+/g, '<ol class="md-ol">$&</ol>')

  // 清理Listas Arrays项之间的所有空白
  html = html.replace(/<\/li>\s+<li/g, '</li><li')
  // 清理Listas Arrays开始标签后的空白
  html = html.replace(/<ul class="md-ul">\s+/g, '<ul class="md-ul">')
  html = html.replace(/<ol class="md-ol">\s+/g, '<ol class="md-ol">')
  // 清理Listas Arrays结束标签前的空白
  html = html.replace(/\s+<\/ul>/g, '</ul>')
  html = html.replace(/\s+<\/ol>/g, '</ol>')
  
  // Parsers negrito / itálico UI
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/_(.+?)_/g, '<em>$1</em>')
  
  // Separar borders style
  html = html.replace(/^---$/gm, '<hr class="md-hr">')
  
  // Ajuste na quebra das linhas - Arrays Values Maps Flow Arrays Arrays Result Method Components Display State Action Formats Display Layout Run Execution Props Outputs Component Returns Action Handle Setup Props Component Props Output Arrays Action State Value String Execution Handling Methods Result Setup Objects Props Variables Logic Process Mapping Render Pattern Value Array Scope Check Execute Flow Logic Array Match Layout Process Loop Setup Response Match Fetch Props Result Call Method Action String Values Object Logic Mapping Object Method Objects Result Loop Value Value Method Display Formats Output Component Displays Execution Return Return Array Handling Logic Values Array Values Run Action Return Method Logic View Method Event Call Logic Response Object Fetch Response Flow Setup Target Data Control Properties Returns Target Map Component Run Event Function Variables Function Method Target Component Prop Values Call Logic Arrays Display Fetch Returns Return Formats Component Objects Flow Scope Functions Returns Scope Function State Scope View Component Handling Array Display Flow Methods Loop Value Properties Results Layout Method Variables Properties <br>
  html = html.replace(/\n\n/g, '</p><p class="md-p">')
  html = html.replace(/\n/g, '<br>')
  
  // Regex Values Function Object Result Loop Output Return Components Map Result Properties Execute Output Render Model Handle String Action Flow View Action Methods Variable Component Output Model Object Event Action Exec Arrays Regex Returns Object Handle Format Execute Handle Setup Displays Output Result Scope Event Logic Fetch Return Props Component Results Mapping Flow Layout Result Method Logic Execution Exec Component Formats Logic View Flow Display Display Results Methods Action Object Setup Pattern Run Execute Formats Returns Returns Variables Array Execute Arrays Regex Rendering Exec Results Action Returns Return Props Arrays Flow Layout Formats View Exec Returns Execute Components Returns Results Render Arrays Results Formats Call Fetch Component
  html = '<p class="md-p">' + html + '</p>'
  
  // Clear Null Text Values Clean Text Regex Parsing Empty Tags Break Strings Code Method Run Layout Render Component Replace Execute Update Flow Variable Component Output Setup Result App Check Format Remove Replace Array Vue Object Variable Flow Execution Output Call Format Action Method Regex Setup Display Return Components Layout Action Target Regex Display Replace Flow Result String Handle App Render Remove Replace Values Target Return DOM Execute Replace Result Flow Variables Response Logic Format View Action Vue App Event Component Component Function App Object Variables DOM Element Event Replace Data Logic
  html = html.replace(/<p class="md-p"><\/p>/g, '')
  html = html.replace(/<p class="md-p">(<h[2-5])/g, '$1')
  html = html.replace(/(<\/h[2-5]>)<\/p>/g, '$1')
  html = html.replace(/<p class="md-p">(<ul|<ol|<blockquote|<pre|<hr)/g, '$1')
  html = html.replace(/(<\/ul>|<\/ol>|<\/blockquote>|<\/pre>)<\/p>/g, '$1')
  // 清理Chunks Format Results Array Handling Data Target Fetch Response Output View Run Exec Flow Component Return Render Variable Object Scope Values Execution Exec Result Function Flow View Render Execute Method Formatting Call Output Exec Prop Variable Results Formatting Handling Value Model Target Data Display Event Fetch Flow Call Mapping Response Mapping Fetch Array DOM Model Execution Fetch Variable Mapping Component Run Flow Output Arrays Map Loop Layout Handle Response Execute Component Handling Output DOM Value Data Object Result Result Variable Event Call Mapping Format Array Arrays Method Setup Variables Exec Output Rendering Execute Output Variables Exec Components Layout Handling Array Match Display Flow Control Function Loop Mapping Action Match Exec Event Output Response View Mapping Formatting Array Render Scope Array Call Data Event Mapping Flow Result Pattern Output Execution Function Pattern Array Function Result Method String Result Format Returns Map Layout级元素前后的 <br> 标签
  html = html.replace(/<br>\s*(<ul|<ol|<blockquote)/g, '$1')
  html = html.replace(/(<\/ul>|<\/ol>|<\/blockquote>)\s*<br>/g, '$1')
  // 清理 <p><br> 紧跟Chunks Format Results Array Handling Data Target Fetch Response Output View Run Exec Flow Component Return Render Variable Object Scope Values Execution Exec Result Function Flow View Render Execute Method Formatting Call Output Exec Prop Variable Results Formatting Handling Value Model Target Data Display Event Fetch Flow Call Mapping Response Mapping Fetch Array DOM Model Execution Fetch Variable Mapping Component Run Flow Output Arrays Map Loop Layout Handle Response Execute Component Handling Output DOM Value Data Object Result Result Variable Event Call Mapping Format Array Arrays Method Setup Variables Exec Output Rendering Execute Output Variables Exec Components Layout Handling Array Match Display Flow Control Function Loop Mapping Action Match Exec Event Output Response View Mapping Formatting Array Render Scope Array Call Data Event Mapping Flow Result Pattern Output Execution Function Pattern Array Function Result Method String Result Format Returns Map Layout级元素的情况（多余空行导致）
  html = html.replace(/<p class="md-p">(<br>\s*)+(<ul|<ol|<blockquote|<pre|<hr)/g, '$2')
  // 清理连续的 <br> 标签
  html = html.replace(/(<br>\s*){2,}/g, '<br>')
  // 清理Chunks Format Results Array Handling Data Target Fetch Response Output View Run Exec Flow Component Return Render Variable Object Scope Values Execution Exec Result Function Flow View Render Execute Method Formatting Call Output Exec Prop Variable Results Formatting Handling Value Model Target Data Display Event Fetch Flow Call Mapping Response Mapping Fetch Array DOM Model Execution Fetch Variable Mapping Component Run Flow Output Arrays Map Loop Layout Handle Response Execute Component Handling Output DOM Value Data Object Result Result Variable Event Call Mapping Format Array Arrays Method Setup Variables Exec Output Rendering Execute Output Variables Exec Components Layout Handling Array Match Display Flow Control Function Loop Mapping Action Match Exec Event Output Response View Mapping Formatting Array Render Scope Array Call Data Event Mapping Flow Result Pattern Output Execution Function Pattern Array Function Result Method String Result Format Returns Map Layout级元素后紧跟的段落开始标签前的 <br>
  html = html.replace(/(<\/ol>|<\/ul>|<\/blockquote>)<br>(<p|<div)/g, '$1$2')

  // 修复非连续有序Listas Arrays的编号：当单项 <ol> 被段落Info隔开时，保持编号递增
  const tokens = html.split(/(<ol class="md-ol">(?:<li class="md-oli"[^>]*>[\s\S]*?<\/li>)+<\/ol>)/g)
  let olCounter = 0
  let inSequence = false
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].startsWith('<ol class="md-ol">')) {
      const liCount = (tokens[i].match(/<li class="md-oli"/g) || []).length
      if (liCount === 1) {
        olCounter++
        if (olCounter > 1) {
          tokens[i] = tokens[i].replace('<ol class="md-ol">', `<ol class="md-ol" start="${olCounter}">`)
        }
        inSequence = true
      } else {
        olCounter = 0
        inSequence = false
      }
    } else if (inSequence) {
      if (/<h[2-5]/.test(tokens[i])) {
        olCounter = 0
        inSequence = false
      }
    }
  }
  html = tokens.join('')

  return html
}

const getTimelineItemClass = (log, idx, total) => {
  const isLatest = idx === total - 1 && !isComplete.value
  const isMilestone = log.action === 'section_complete' || log.action === 'report_complete'
  return {
    'node--active': isLatest,
    'node--done': !isLatest && isMilestone,
    'node--muted': !isLatest && !isMilestone,
    'node--tool': log.action === 'tool_call' || log.action === 'tool_result'
  }
}

const getConnectorClass = (log, idx, total) => {
  const isLatest = idx === total - 1 && !isComplete.value
  if (isLatest) return 'dot-active'
  if (log.action === 'section_complete' || log.action === 'report_complete') return 'dot-done'
  return 'dot-muted'
}

const getActionLabel = (action) => {
  const labels = {
    'report_start': 'Report Started',
    'planning_start': 'Planning',
    'planning_complete': 'Plan Complete',
    'section_start': 'Section Start',
    'section_content': 'Content Ready',
    'section_complete': 'Section Done',
    'tool_call': 'Tool Call',
    'tool_result': 'Tool Result',
    'llm_response': 'LLM Response',
    'report_complete': 'Complete'
  }
  return labels[action] || action
}

const getLogLevelClass = (log) => {
  if (log.includes('ERROR') || log.includes('Falha')) return 'error'
  if (log.includes('WARNING') || log.includes('CUIDADO')) return 'warning'
  // INFO Cor base livre de labels success
  return ''
}

// Contamination-safe content rendering
const renderSafeSectionContent = (sectionIndex) => {
  const content = generatedSections.value[sectionIndex]
  if (!content) return ''
  
  // Check if we already validated this section
  if (contaminatedSections.value.has(sectionIndex)) {
    // Return empty - the warning will be shown instead
    return ''
  }
  
  // Validate the content
  const contamination = detectContamination(content, {
    maxLength: 100000,
    checkRepetition: true,
    checkEncoding: true,
    checkInjection: true
  })
  
  if (contamination.severity === 'critical') {
    // Mark as contaminated and return empty
    contaminatedSections.value.add(sectionIndex)
    sectionWarnings[sectionIndex] = {
      reason: contamination.reasons.join(', '),
      severity: 'critical'
    }
    return ''
  }
  
  if (contamination.severity === 'warning') {
    // Store warning info for UI display
    sectionWarnings[sectionIndex] = {
      reason: contamination.reasons.join(', '),
      severity: 'warning'
    }
    // Sanitize and render
    const sanitized = sanitizeContent(content)
    return renderMarkdown(sanitized)
  }
  
  // Clean content - render normally
  return renderMarkdown(content)
}

// Polling
let agentLogTimer = null
let consoleLogTimer = null

const fetchAgentLog = async () => {
  if (!props.reportId) return
  
  try {
    const res = await getAgentLog(props.reportId, agentLogLine.value)
    
    if (res.success && res.data) {
      const newLogs = res.data.logs || []
      
      if (newLogs.length > 0) {
        newLogs.forEach(log => {
          agentLogs.value.push(log)
          
          if (log.action === 'planning_complete' && log.details?.outline) {
            reportOutline.value = log.details.outline
          }
          
          if (log.action === 'section_start') {
            currentSectionIndex.value = log.section_index
          }

          // section_complete - State Updates View Render Variables Formats Maps Target Handling Mapping Value Returns Function Properties Component Prop Call Results Methods Action Displays Object Event Components Array Props Setup Displays Objects Returns Logic Fetch Run Loop Flow Values Mapping Returns Results Mapping Function Flow Logic Action Event Component Map State Results Response Mapping Scope Loop Object Handling State Map Display Rendering Scope Data Objects Layout Execution Execute Formatting Components Layout Execute Render View Component Values Output Return Rendering Outputs Results Execution Output Props Execute Function Setup Loop Map Methods Displays Fetch Event Object Props Maps Arrays Data Flow Action Values Target Returns Event Displays Logic Regex Handling Return Layout Handling Props Pattern View Action Data State Handling Loop Handling Action Displays Mapping Control Returns Mapping Mapping Control Logic Values View Exec Arrays Execution Formatting Method Values State Output Component Handling Map Function Components Mapping Components Properties Output Prop Flow Object Setup Mapping Map Array Output Functions Response Method Display Data Mapping Variables Control Arrays Flow Array Execution Variables Component Loop Array Method Logic Methods
          if (log.action === 'section_complete') {
            if (log.details?.content) {
              generatedSections.value[log.section_index] = log.details.content
              // Open Tab Docs Output Auto Expand Accordeon Div CSS Classes Watch Value Changed Hooks Appends Layout Recreate Transition View Logic
              expandedContent.value.add(log.section_index - 1)
              currentSectionIndex.value = null
            }
          }
          
          if (log.action === 'report_complete') {
            isComplete.value = true
            currentSectionIndex.value = null  // Força clear spinners
            emit('update-status', 'completed')
            stopPolling()
            // Component Control Object Setup Outputs Fetch Target Execute Event Component Array Control Execution Arrays Run Logic Handling Output Setup Components Variables Component Target Properties Render Map Outputs Logic Props Map Fetch Process Method Displays Map Functions Logic Formats Object Variables String Setup Variable Return Mapping Results Check Props Mapping Formats Return String Action Methods Variables Logic Process Mapping Setup Prop Pattern Response String Handling Variables Method Layout Action Results Objects Output Object Props Prop Output Arrays Execute Variable Components Array Displays Exec Arrays Return Results Array Mapping Outputs Component Flow Arrays Execute Run Methods Output Response Logic Variables View Map Value Formats Logic Regex Format Check Event Target Exec Object Results Call Handling Result Run Returns Execute Display Match Formatting Handle Data Formats Call Array Check Target Exec
          }
          
          if (log.action === 'report_start') {
            startTime.value = new Date(log.timestamp)
          }
        })
        
        agentLogLine.value = res.data.from_line + newLogs.length
        
        nextTick(() => {
          if (rightPanel.value) {
            // Top Scroll / If Valid Flow End Point Render Actions Control Window ScrollTo API UsedRodapé da leituraFlow Components Fetch Regex Method Exec Display Setup Setup Component Component App Component Fetch Layout Functions Method Methods Scope Prop Fetch Map String Display Execution String Code Outputs Setup Data Object Scope Result Display Return Formatting Target Outputs Execute Format Run Map Objects Prop Check Flow Objects Return Fetch Mapping Format Setup View Render Variables Displays Display Check Variable Method Process Handling Return Render Flow Maps Method Displays Result Event Mapping Action State Execution Map Run Execute String Result Fetch Pattern Target Mapping Exec Formats Response Event Arrays Objects Check String Variable Run Control Fetch Outputs Action Run Formats Call Object Flow Display Variables Result Object Returns Mapping Properties Return Handling Variables Setup Methods Variables Process Format Execution State Outputs Match
            if (isComplete.value) {
              rightPanel.value.scrollTop = 0
            } else {
              rightPanel.value.scrollTop = rightPanel.value.scrollHeight
            }
          }
        })
      }
    }
  } catch (err) {
    console.warn('Failed to fetch agent log:', err)
  }
}

// Sacar veredicto - Function Loop Call Prop Execute Rendering String Render Displays Functions Displays Method Object Format Methods Response Logic Result Component Setup Variables Display Array Object Display Variables Arrays Values Components Format Run Prop Array Setup Exec Setup Method Display Check Action Value Components Event Event Object Output Process Target Output Component Logic Properties Regex Displays Return Return Check Outputs Action Render View Arrays Result App Variable Output String Control Display Array Output Object View Data Component Check Scope Functions Object Functions Formatting Event Setup Returns Method Props Mapping Output Fetch Return Call Maps Data Function Event Call Display Properties Call Logic Return Mapping Objects Event Data Result Mapping Call Execution String Pattern Mapping Properties Map Call Rendering Render Formatting State Method Formatting Component Formatting Outputs Data Target Fetch Property Run Execute Format Methods Output Rendering Formats Output Values Code Property Handling Rendering Setup View Returns Flow Fetch Arrays Object Flow Outputs Components String Run Returns Display Action
const extractFinalContent = (response) => {
  if (!response) return null
  
  // Displays Layout Result Process Target Value Output Mapping Functions Map Fetch Formats Exec Output Target Returns Displays Value Fetch Loop Fetch Props Render Displays Run Component Model Methods Control Outputs Return Mapping Execution Run Rendering Props Model Returns Properties Setup Component Object Fetch Mapping Execution Method Handle Action State Fetch Setup Object Setup Model Components Array Pattern Objects Data Target Process Flow Props Variables Process View Results Handle Control Scope Formats Prop Properties Data Action Displays Execution Variable Output Output Array Data Method Model Action Returns View Run String Formats Match Model Process Array Properties Logic Control Execute Fetch Results Component Layout Exec Data Layout Method Formats Arrays Returns Variables Action Displays Logic Target Output Exec Output String Render Functions String Render Function Variables Check Call Logic Check Method View Render Method Displays Handling Control Variables Data Call Execution Match Control Arrays Fetch Logic Execute Pattern Returns Logic Loop Formats Methods Process Run Scope View Results Array Flow Layout Action Output Exec Mapping Layout Scope Returns Result Handle Values Flow Value Outputs Logic Data Control Displays Scope Format Formats Method Fetch Function Formatting Event Properties Logic Formatting Display Control State Data Arrays Return Returns Target Map Arrays Flow Result View Object Logic Prop Process Object Displays Flow Target Variable Map Function Execution Logic Process Properties View Return Variables Render Handle Methods Mapping Layout Function Match App Variable Object Data Response Check Values Mapping Setup Call Layout Outputs Result Components <final_answer> Prop Arrays Functions Return Handling Target Returns Method Rendering Flow Exec Target Output Event Format Results Setup Action Display Fetch Maps Pattern Loop Map Response Execute Output Target Format Action Handling Displays Setup Setup Execute Exec String Rendering Methods Arrays Output Displays Arrays Call Call Mapping Method Action Fetch Control Mapping Process Return Setup Component State Layout Check View View App Variables Component Return Mapping Value Response State Map Display Execution Check Variables Map Layout Output Scope Result Call Result Returns String Output Flow Format Render Handling Action Run Method Mapping Formats Data Fetch Fetch Handling Event Run Prop Map Display Format Format Loop Output Model State Displays Execution Component Data Component Function Format Variable Mapping String Setup Variables Outputs Logic Action String Process Result Components Action Execute Run Setup Scope String Outputs Variable Result Mapping Mapping Variable Setup Objects Event Setup Handling Object Outputs
  const finalAnswerTagMatch = response.match(/<final_answer>([\s\S]*?)<\/final_answer>/)
  if (finalAnswerTagMatch) {
    return finalAnswerTagMatch[1].trim()
  }
  
  // Results Prop Map Object Logic Methods Method Event Logic Action Results Format Array Exec Results Setup Match Result Call Regex Mapping Output Output Output Return Action Handling Call Component Execute Fetch Handling Setup Arrays Props Check Handling Result View Display Handle Components Logic Values Results Action Match Component Output View Event Execute Formatting Execute Logic String Output Exec Code Display Formats Run Returns Arrays Process Target Run Components Array Fetch Formatting Variables Rendering Display Returns Methods Mapping Array Output Output Flow Setup Event Map Components Results Call Loop Array Layout Check Code Run Methods Properties Scope Objects Execution Mapping Fetch Flow Variable Fetch Display Model Formatting Scope Event Objects Target Execution Action Formats Method Return Flow Variables Display Exec Output Results Logic Rendering Display Model Methods Action State Loop Layout Pattern Layout Execute Final Answer: Corpo a seguir (suporta markdown e afins)）
  // 格式1: Final Answer:\n\nInfo
  // 格式2: Final Answer: Info
  const finalAnswerMatch = response.match(/Final\s*Answer:\s*\n*([\s\S]*)$/i)
  if (finalAnswerMatch) {
    return finalAnswerMatch[1].trim()
  }
  
  // Setup Execution Regex Fetch Model Format Values Data Displays Data Object Prop Response Results Pattern Object Data Array Process Result Execute Check Properties Formatting Result Fetch Handling Render Response Exec Function Logic Format Objects Layout Display Mapping Call Result Action Array Result Returns Execute Event Array Regex Render Properties Component Logic Map Exec Action Methods Execute Results Format Map Array Formatting Output Setup Logic Returns Fetch Response Output Handling Scope Call Array Properties Values Methods Layout Variables Flow Components Display Handling Check Event Exec Handling Function View Displays Output Component Call Mapping Match Properties Output Logic Call Event Mapping Exec Component Logic Scope Action App Object Layout Component View Function Component Run Regex Render Model Fetch App Event Call Response Action Variables App Result Model Arrays String Display Data Mapping Setup Flow Components Event Values Flow Response Results Model Objects View Prop Returns Object Formats Values Flow Exec Formats Render Display App Loop Function: Restante Box Info
  const chineseFinalMatch = response.match(/Components View Code Mapping App Prop Map Object Process Setup Method App Map Results String Results Methods Call Control Component Display Results Return Output Formatting Logic Map Value Setup Maps Result Method Layout Prop Values Display Response Components Result Method Mapping Layout Methods Render Variables Action Arrays Target Pattern Results Format Exec Variables Action View Variables Logic Variables Run Map Handling Fetch Component Displays Flow Handling Setup Exec Object Exec View Action Object Output Fetch Data Execute Variable Component Setup Flow Format Returns App Logic Method Exec Event Object Action Handling Results Execution Flow Handling Response Scope Layout Response Execute String Displays Formats Returns Call Method Display Exec Handle Logic Fetch Action Component Array Check Formats Setup Handling Setup Map Object Handling Code Method Check Prop Returns Map Fetch Call Display Logic Exec Run Loop Check Execute Flow Object Formatting Functions View Properties Display String Execute Variables Display State Pattern Object Setup Execute Displays Handle Output Result Scope Mapping Arrays Render Method Action Results Process Process Loop Execution Response Return Handling Prop Logic Mapping Props Output Action Run Match Output Event Result Logic Match Function Execution Output App Function Mapping Outputs Event Handling Layout Values Object Displays Execution Fetch Target Values Logic Handling Layout Flow Setup Loop[:：]\s*\n*([\s\S]*)$/i)
  if (chineseFinalMatch) {
    return chineseFinalMatch[1].trim()
  }
  
  // Response Action Mapping Object Return Check Outputs Process Object Values Layout Render Map Output Object Output Component Variables Call Rendering Model Event Result Event Execute Logic Array Format View Function Formats Exec Methods Call Output Exec Rendering Handle Flow Arrays Component Return Action Function Map Layout Setup Formatting Displays String Mapping Object Mapping Arrays Execution Output Logic Execution Call Returns Object Loop Exec Value Handle Outputs Fetch State Action Call Component Fetch Method Output Check Execution Setup Fetch Target Handling Mapping Map Component String Displays Formatting Method Fetch Flow String Methods Flow Execute Output Arrays Scope Prop Execution Variables Event Result Setup Call Result Object Fetch Flow Variables Regex App Logic Check Prop App Returns Map Methods Return Variable Code Value Flow ## Verso # Verso > Start Text Markdown Code Setup Output Response View Target Render Function Regex Array Value Format HTML Output Block Format Execution Code Parsing Vue Setup Target Run App Method Render Output Component Event DOM Check Handle Result Format Call Output Execution Values Regex Vue Event Layout Output String Object Component Render Result Method Target Action Output Object Replace Check String Properties Variables Components Replace Data Setup Value Replace Response Array Component Vue Flow Process Action Text Replace Regex Vue Data Execution View Target Run
  const trimmedResponse = response.trim()
  if (trimmedResponse.match(/^[#>]/)) {
    return trimmedResponse
  }
  
  // Map Display Displays Methods Logic Logic Outputs Action Properties Outputs Check Value Process Displays Array Props Value Variables Results Results Displays Displays Mapping Objects Displays Process Execute Results Execution Objects Object Return Returns Process Displays Values Execution Flow Setup Component Layout Response Components Process Array Objects Displays Displays Function Handling Object Result Output Displays Results Displays Target Function Method Properties Flow Output Objects Exec Methods Code Call Run Displays Function Properties Output Flow Result Displays Maps Prop Map Displays Method Exec Logic Action Method Object Prop Execute Map Objects Format Method Mapping Return Check Arrays Loop Loop Value Exec Process Properties Setup Execution Function Mapping Components Render Setup Action Action Map Handling Results Flow Response Execution Variable Formats Format Props Array Execute Target Target Mapping Props Call Return Method View Array Arrays Call Output Formats Regex Result Loop Variables Arrays Mapping Function Mapping Scope Run Execution Method Display Exec Props Variables Results Returns Methods Prop Prop Format Execution Props Loop Event Map Handle Setup Variables Array Return Loop Scope Components Object Handle Displays Exec Map Call Function Execute Loop Action Scope App Target Variable Mapping Regex Map Target Mapping Return Flow Handle Results Exec Objects State Logic Format View Return Method View Formats Properties Execution Loop Map Target Function Setup Objects Call Function Formats Array Flow Function Scope Object Object View Logic Event Scope Check Component Maps Response Map Variables Function Logic Object Handle Match Prop Output Event Outputs Output Exec Execution Display Target Flow Array
  if (response.length > 300 && (response.includes('**') || response.includes('>'))) {
    // Map Value Functions Data Fetch Mapping Results Method Handling Variable Return Object Render Properties Output Formats Event Logic Execution Pattern Match Output Result Target Data Action Check Process Setup State Fetch View Displays Object Map Formats Outputs Action Returns Methods Response Event Run Arrays Logic Match Process Code Components View Rendering Action Check Call Display Method Pattern Functions Target Layout Target Method Output Call Displays Values Returns Methods Component Functions Results Handling Displays Formats Array Map Call Check Execution String Flow Variables Returns Return Flow Properties Action Response Fetch Execution Fetch Execute Scope Outputs Values Format Flow Target Props Component Method Fetch Handling Results Regex Formats Code Scope Value Setup Component Result Output Execution Methods Event Match Setup Return Exec Arrays Object Displays Fetch Pattern Component Setup Objects Value Check Target Regex Functions Formats Props Objects Response Execution View Process Logic Loop Setup Return Match Method Returns Variables Display Function Variables Objects String Object Event Mapping Data Code Return Thought: Mapping Value Logic Execution Props Execute Arrays Formats Functions Target Setup Output Object Result Methods Formatting Run Scope Logic Output Loop Component Output Values Process Method Fetch Render Logic Handling String Response Components Logic Value Handling Event Arrays Result Return Method Render Object Flow Map Pattern Flow Method Run Map Layout Setup Call Fetch Functions Method Result Outputs Values Properties State Fetch Setup Outputs Variables Results Setup Setup Mapping Result Call Returns Formats Handle Result Handling Component Response Object Handling Call Process Setup Event Execute Return Action String Check Handling Flow Results Output Response Mapping Pattern Results Results Object Handling Outputs Response Pattern Data Results Formatting Scope Check Loop Method Data Logic
    const thoughtMatch = response.match(/^Thought:[\s\S]*?(?=\n\n[^T]|\n\n$)/i)
    if (thoughtMatch) {
      const afterThought = response.substring(thoughtMatch[0].length).trim()
      if (afterThought.length > 100) {
        return afterThought
      }
    }
  }
  
  return null
}

const fetchConsoleLog = async () => {
  if (!props.reportId) return
  
  try {
    const res = await getConsoleLog(props.reportId, consoleLogLine.value)
    
    if (res.success && res.data) {
      const newLogs = res.data.logs || []
      
      if (newLogs.length > 0) {
        consoleLogs.value.push(...newLogs)
        consoleLogLine.value = res.data.from_line + newLogs.length
        
        nextTick(() => {
          if (logContent.value) {
            logContent.value.scrollTop = logContent.value.scrollHeight
          }
        })
      }
    }
  } catch (err) {
    console.warn('Failed to fetch console log:', err)
  }
}

const startPolling = () => {
  if (agentLogTimer || consoleLogTimer) return
  
  fetchAgentLog()
  fetchConsoleLog()
  
  agentLogTimer = setInterval(fetchAgentLog, 2000)
  consoleLogTimer = setInterval(fetchConsoleLog, 1500)
}

const stopPolling = () => {
  if (agentLogTimer) {
    clearInterval(agentLogTimer)
    agentLogTimer = null
  }
  if (consoleLogTimer) {
    clearInterval(consoleLogTimer)
    consoleLogTimer = null
  }
}

// Lifecycle
onMounted(() => {
  if (props.reportId) {
    addLog(`Report Agent initialized: ${props.reportId}`)
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

watch(() => props.reportId, (newId) => {
  if (newId) {
    agentLogs.value = []
    consoleLogs.value = []
    agentLogLine.value = 0
    consoleLogLine.value = 0
    reportOutline.value = null
    currentSectionIndex.value = null
    generatedSections.value = {}
    expandedContent.value = new Set()
    expandedLogs.value = new Set()
    collapsedSections.value = new Set()
    isComplete.value = false
    startTime.value = null
    
    startPolling()
  }
}, { immediate: true })
</script>

<style scoped>
.report-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-container-low);
  font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif;
  overflow: hidden;
}

/* Main Split Layout */
.main-split-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Panel Headers */
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-on-background);
  box-shadow: 0 0 0 3px rgba(31, 41, 55, 0.15);
  margin-right: 10px;
  flex-shrink: 0;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(31, 41, 55, 0.15);
  }
  50% {
    box-shadow: 0 0 0 5px rgba(31, 41, 55, 0.1);
  }
}

.header-index {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-disabled);
  margin-right: 10px;
  flex-shrink: 0;
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: none;
  letter-spacing: 0;
}

.header-meta {
  margin-left: auto;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-muted);
  flex-shrink: 0;
}

/* Panel header status variants */
.panel-header--active {
  background: var(--color-surface-container-low);
  border-color: var(--color-on-background);
}

.panel-header--active .header-index {
  color: var(--color-on-background);
}

.panel-header--active .header-title {
  color: var(--color-on-background);
}

.panel-header--active .header-meta {
  color: var(--color-on-background);
}

.panel-header--done {
  background: var(--color-surface-container-low);
}

.panel-header--done .header-index {
  color: var(--color-success);
}

.panel-header--todo .header-index,
.panel-header--todo .header-title {
  color: var(--color-disabled);
}

/* Left Panel - Report Style */
.left-panel.report-style {
  width: 45%;
  min-width: 450px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-outline);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 30px 50px 60px 50px;
}

.left-panel::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track {
  background: transparent;
}

.left-panel::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.3s ease;
}

.left-panel:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

/* Report Header */
.report-content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.report-header-block {
  margin-bottom: 30px;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.report-tag {
  background: var(--color-on-background);
  color: var(--color-surface);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.report-id {
  font-size: 11px;
  color: var(--color-disabled);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.main-title {
  font-family: 'Times New Roman', Times, serif;
  font-size: 36px;
  font-weight: 700;
  color: var(--color-on-background);
  line-height: 1.2;
  margin: 0 0 16px 0;
  letter-spacing: -0.02em;
}

.sub-title {
  font-family: 'Times New Roman', Times, serif;
  font-size: 16px;
  color: var(--color-muted);
  font-style: italic;
  line-height: 1.6;
  margin: 0 0 30px 0;
  font-weight: 400;
}

.header-divider {
  height: 1px;
  background: var(--color-outline);
  width: 100%;
}

/* Sections List */
.sections-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.report-section-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: var(--space-4);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.report-section-item:hover {
  box-shadow: var(--shadow-sm);
}

/* Due-diligence accent borders */
.report-section-item.dd-tese {
  border-left: 3px solid var(--color-primary);
}

.report-section-item.dd-evidencias {
  border-left: 3px solid var(--color-success);
}

.report-section-item.dd-fragilidades {
  border-left: 3px solid var(--color-error);
}

.report-section-item.dd-premissas {
  border-left: 3px solid var(--color-warning);
}

.report-section-item.dd-cenarios {
  border-left: 3px solid var(--color-info);
}

.dd-badge {
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px 8px;
  background: var(--color-surface-container-low);
  color: var(--color-muted);
  margin-left: auto;
}

.section-header-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  transition: background-color 0.2s ease;
  padding: 8px 12px;
  margin: -8px -12px;
  border-radius: 8px;
}

.section-header-row.clickable {
  cursor: pointer;
}

.section-header-row.clickable:hover {
  background-color: var(--color-surface-container-low);
}

.collapse-icon {
  margin-left: auto;
  color: var(--color-disabled);
  transition: transform 0.3s ease;
  flex-shrink: 0;
  align-self: center;
}

.collapse-icon.is-collapsed {
  transform: rotate(-90deg);
}

.section-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  color: var(--color-disabled); /* Color scale fix gray status nonreactive */
  font-weight: 500;
}

.section-title {
  font-family: 'Times New Roman', Times, serif;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-on-background);
  margin: 0;
  transition: color 0.3s ease;
}

/* States */
.report-section-item.is-pending .section-title {
  color: var(--color-outline);
}

.report-section-item.is-active .section-title,
.report-section-item.is-completed .section-title {
  color: var(--color-on-background);
}

.section-body {
  padding-left: 28px;
  overflow: hidden;
}

/* Generated Content */
.generated-content {
  font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-on-surface);
}

.generated-content :deep(p) {
  margin-bottom: 1em;
}

.generated-content :deep(.md-h2),
.generated-content :deep(.md-h3),
.generated-content :deep(.md-h4) {
  font-family: 'Times New Roman', Times, serif;
  color: var(--color-on-background);
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  font-weight: 700;
}

.generated-content :deep(.md-h2) { font-size: 20px; border-bottom: 1px solid var(--color-surface-container-low); padding-bottom: 8px; }
.generated-content :deep(.md-h3) { font-size: 18px; }
.generated-content :deep(.md-h4) { font-size: 16px; }

.generated-content :deep(.md-ul),
.generated-content :deep(.md-ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.generated-content :deep(.md-li),
.generated-content :deep(.md-oli) {
  margin: 6px 0;
}

.generated-content :deep(.md-quote) {
  border-left: 3px solid var(--color-outline);
  padding-left: 16px;
  margin: 1.5em 0;
  color: var(--color-muted);
  font-style: italic;
  font-family: 'Times New Roman', Times, serif;
}

.generated-content :deep(.code-block) {
  background: var(--color-surface-container-low);
  padding: 12px;
  border-radius: 0px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid var(--color-outline);
}

.generated-content :deep(strong) {
  font-weight: 600;
  color: var(--color-on-background);
}

/* Loading State */
.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-muted);
  font-size: 14px;
  margin-top: 4px;
}

.loading-icon {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-family: 'Times New Roman', Times, serif;
  font-size: 15px;
  color: var(--color-muted);
}

.cursor-blink {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: var(--color-info);
  opacity: 0.5;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Content Styles Override for this view */
.generated-content :deep(.md-h2) {
  font-family: 'Times New Roman', Times, serif;
  font-size: 18px;
  margin-top: 0;
}


/* Slide Content Transition */
.slide-content-enter-active {
  transition: opacity 0.3s ease-out;
}

.slide-content-leave-active {
  transition: opacity 0.2s ease-in;
}

.slide-content-enter-from,
.slide-content-leave-to {
  opacity: 0;
}

.slide-content-enter-to,
.slide-content-leave-from {
  opacity: 1;
}

/* Waiting Placeholder */
.waiting-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 40px;
  color: var(--color-disabled);
}

.waiting-animation {
  position: relative;
  width: 48px;
  height: 48px;
}

.waiting-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid var(--color-outline);
  border-radius: 50%;
  animation: ripple 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.waiting-ring:nth-child(2) {
  animation-delay: 0.4s;
}

.waiting-ring:nth-child(3) {
  animation-delay: 0.8s;
}

@keyframes ripple {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}

.waiting-text {
  font-size: 14px;
}

/* Right Panel */
.right-panel {
  flex: 1;
  background: var(--color-surface);
  overflow-y: auto;
  display: flex;
  flex-direction: column;

  /* Functional palette (low saturation, status-based) */
  --wf-border: var(--color-outline);
  --wf-divider: var(--color-surface-container-low);

  --wf-active-bg: var(--color-surface-container-low);
  --wf-active-border: var(--color-on-background);
  --wf-active-dot: var(--color-on-background);
  --wf-active-text: var(--color-on-background);

  --wf-done-bg: var(--color-surface-container-low);
  --wf-done-border: var(--color-outline);
  --wf-done-dot: var(--color-success);

  --wf-muted-dot: var(--color-outline);
  --wf-todo-text: var(--color-disabled);
}

.right-panel::-webkit-scrollbar {
  width: 6px;
}

.right-panel::-webkit-scrollbar-track {
  background: transparent;
}

.right-panel::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.3s ease;
}

.right-panel:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
}

.right-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

.mono {
  font-family: 'JetBrains Mono', monospace;
}

/* Workflow Overview */
.workflow-overview {
  padding: 16px 20px 0 20px;
}

.workflow-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.metric {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
}

.metric-right {
  margin-left: auto;
}

.metric-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-disabled);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.metric-value {
  font-size: 12px;
  color: var(--color-on-surface);
}

.metric-pill {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--wf-border);
  background: var(--color-surface-container-low);
  color: var(--color-muted);
}

.metric-pill.pill--processing {
  background: var(--wf-active-bg);
  border-color: var(--wf-active-border);
  color: var(--wf-active-text);
}

.metric-pill.pill--completed {
  background: var(--color-success-bg);
  border-color: var(--color-success);
  color: var(--color-success);
}

.metric-pill.pill--pending {
  background: transparent;
  border-style: dashed;
  color: var(--color-muted);
}

.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 10px;
}

.wf-step {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--wf-divider);
  border-radius: 8px;
  background: var(--color-surface);
}

.wf-step--active {
  background: var(--wf-active-bg);
  border-color: var(--wf-active-border);
}

.wf-step--done {
  background: var(--wf-done-bg);
  border-color: var(--wf-done-border);
}

.wf-step--todo {
  background: transparent;
  border-color: var(--wf-border);
  border-style: dashed;
}

.wf-step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.wf-step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--wf-muted-dot);
  border: 2px solid var(--color-surface);
  z-index: 1;
}

.wf-step-line {
  width: 2px;
  flex: 1;
  background: var(--wf-divider);
  margin-top: -2px;
}

.wf-step--active .wf-step-dot {
  background: var(--wf-active-dot);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.wf-step--done .wf-step-dot {
  background: var(--wf-done-dot);
}

.wf-step-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.wf-step-index {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-disabled);
  letter-spacing: 0.02em;
  flex-shrink: 0;
}

.wf-step-title {
  font-family: 'Times New Roman', Times, serif;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-background);
  line-height: 1.35;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wf-step-meta {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  color: var(--wf-active-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.wf-step--todo .wf-step-title,
.wf-step--todo .wf-step-index {
  color: var(--wf-todo-text);
}

.workflow-divider {
  height: 1px;
  background: var(--wf-divider);
  margin: 14px 0 0 0;
}

/* Workflow Timeline */
.workflow-timeline {
  padding: 14px 20px 24px;
  flex: 1;
}

.timeline-item {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  border: 1px solid var(--wf-divider);
  border-radius: 8px;
  background: var(--color-surface);
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.timeline-item:hover {
  background: var(--color-surface-container-low);
  border-color: var(--wf-border);
}

.timeline-item.node--active {
  background: var(--wf-active-bg);
  border-color: var(--wf-active-border);
}

.timeline-item.node--active:hover {
  background: var(--wf-active-bg);
  border-color: var(--wf-active-border);
}

.timeline-item.node--done {
  background: var(--wf-done-bg);
  border-color: var(--wf-done-border);
}

.timeline-item.node--done:hover {
  background: var(--wf-done-bg);
  border-color: var(--wf-done-border);
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.connector-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--wf-muted-dot);
  border: 2px solid var(--color-surface);
  z-index: 1;
}

.connector-line {
  width: 2px;
  flex: 1;
  background: var(--wf-divider);
  margin-top: -2px;
}

/* Connector dot: status only */
.dot-active {
  background: var(--wf-active-dot);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.dot-done {
  background: var(--wf-done-dot);
}

.dot-muted {
  background: var(--wf-muted-dot);
}

.timeline-content {
  min-width: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin: 0;
  transition: none;
}

.timeline-content:hover {
  box-shadow: none;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.action-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.action-time {
  font-size: 11px;
  color: var(--color-disabled);
  font-family: 'JetBrains Mono', monospace;
}

.timeline-body {
  font-size: 13px;
  color: var(--color-muted);
}

.timeline-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--color-surface-container-low);
}

.elapsed-placeholder {
  flex-shrink: 0;
}

.footer-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.elapsed-badge {
  font-size: 11px;
  color: var(--color-muted);
  background: var(--color-surface-container-low);
  padding: 2px 8px;
  border-radius: 10px;
  font-family: 'JetBrains Mono', monospace;
}

/* Timeline Body Elements */
.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.info-key {
  font-size: 11px;
  color: var(--color-disabled);
  min-width: 80px;
}

.info-val {
  color: var(--color-on-surface);
}

.status-message {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid transparent;
}

.status-message.planning {
  background: var(--wf-active-bg);
  border-color: var(--wf-active-border);
  color: var(--wf-active-text);
}

.status-message.success {
  background: var(--color-success-bg);
  border-color: var(--color-success);
  color: var(--color-success);
}

.outline-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 10px;
  background: var(--color-surface-container-low);
  color: var(--color-muted);
  border: 1px solid var(--color-outline);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--wf-border);
  border-radius: 6px;
}

.section-tag.content-ready {
  background: var(--wf-active-bg);
  border: 1px dashed var(--wf-active-border);
}

.section-tag.content-ready svg {
  color: var(--wf-active-dot);
}


.section-tag.completed {
  background: var(--color-success-bg);
  border: 1px solid var(--color-success);
}

.section-tag.completed svg {
  color: var(--color-success);
}

.tag-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-muted);
}

.section-tag.completed .tag-num {
  color: var(--color-success);
}

.tag-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-on-surface);
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-surface-container-low);
  color: var(--color-on-surface);
  border: 1px solid var(--wf-border);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tool-icon {
  flex-shrink: 0;
}

/* Tool Colors - Purple (Deep Insight) */
.tool-badge.tool-purple {
  background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
  border-color: #C4B5FD;
  color: var(--color-info);
}
.tool-badge.tool-purple .tool-icon {
  stroke: var(--color-info);
}

/* Tool Colors - Blue (Panorama Search) */
.tool-badge.tool-blue {
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  border-color: #93C5FD;
  color: var(--color-info);
}
.tool-badge.tool-blue .tool-icon {
  stroke: var(--color-info);
}

/* Tool Colors - Green (Agent Interview) */
.tool-badge.tool-green {
  background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
  border-color: #86EFAC;
  color: #15803D;
}
.tool-badge.tool-green .tool-icon {
  stroke: var(--color-success);
}

/* Tool Colors - Orange (Quick Search) */
.tool-badge.tool-orange {
  background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
  border-color: #FDBA74;
  color: var(--color-warning);
}
.tool-badge.tool-orange .tool-icon {
  stroke: var(--color-warning);
}

/* Tool Colors - Cyan (Graph Stats) */
.tool-badge.tool-cyan {
  background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%);
  border-color: #67E8F9;
  color: #0E7490;
}
.tool-badge.tool-cyan .tool-icon {
  stroke: #0891B2;
}

/* Tool Colors - Pink (Entity Query) */
.tool-badge.tool-pink {
  background: linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%);
  border-color: #F9A8D4;
  color: #BE185D;
}
.tool-badge.tool-pink .tool-icon {
  stroke: #DB2777;
}

/* Tool Colors - Gray (Default) */
.tool-badge.tool-gray {
  background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
  border-color: var(--color-outline);
  color: var(--color-on-surface);
}
.tool-badge.tool-gray .tool-icon {
  stroke: var(--color-muted);
}

.tool-params {
  margin-top: 10px;
  background: transparent;
  border-radius: 0;
  padding: 10px 0 0 0;
  border-top: 1px dashed var(--wf-divider);
  overflow-x: auto;
}

.tool-params pre {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--color-muted);
  white-space: pre-wrap;
  word-break: break-all;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  padding: 10px;
}

/* Unified Action Buttons */
.action-btn {
  background: var(--color-on-background);
  border: none;
  padding: 4px 10px;
  border-radius: 0px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-machine);
  color: var(--color-surface-container-highest);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.action-btn:hover {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

/* Result Wrapper */
.result-wrapper {
  background: transparent;
  border: none;
  border-top: 1px solid var(--wf-divider);
  border-radius: 0;
  padding: 12px 0 0 0;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-tool {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.result-size {
  font-size: 10px;
  color: var(--color-muted);
  font-family: 'JetBrains Mono', monospace;
}

.result-raw {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.result-raw pre {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-on-surface);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: 10px;
  border-radius: 6px;
}

.raw-preview {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-muted);
}

/* Legacy toggle-raw removed - using unified .action-btn */

/* LLM Response */
.llm-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 11px;
  padding: 3px 8px;
  background: var(--color-surface-container-low);
  color: var(--color-muted);
  border-radius: 4px;
}

.meta-tag.active {
  background: var(--color-info-bg);
  color: #1E40AF;
}

.meta-tag.final-answer {
  background: #D1FAE5;
  color: var(--color-success);
  font-weight: 600;
}

.final-answer-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 10px 14px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success);
  border-radius: 6px;
  color: var(--color-success);
  font-size: 12px;
  font-weight: 500;
}

.final-answer-hint svg {
  flex-shrink: 0;
}

.llm-content {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.llm-content pre {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-muted);
  background: var(--color-surface-container-low);
  padding: 10px;
  border-radius: 6px;
}

/* Complete Banner */
.complete-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success);
  border-radius: 8px;
  color: var(--color-success);
  font-weight: 600;
  font-size: 14px;
}

.next-step-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: calc(100% - 40px);
  margin: 4px 20px 0 20px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-machine);
  color: var(--color-surface-container-highest);
  background: var(--color-on-background);
  border: none;
  border-radius: 0px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.next-step-btn:hover {
  background: var(--color-background);
  color: var(--color-on-background);
  box-shadow: 4px 4px 0 var(--color-on-background);
}

.next-step-btn svg {
  transition: transform 0.2s ease;
}

.next-step-btn:hover svg {
  transform: translateX(4px);
}

/* Workflow Empty */
.workflow-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--color-disabled);
  font-size: 13px;
}

.empty-pulse {
  width: 24px;
  height: 24px;
  background: var(--color-outline);
  border-radius: 50%;
  margin-bottom: 16px;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
}

/* Timeline Transitions */
.timeline-item-enter-active {
  transition: all 0.4s ease;
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

/* ========== Structured Result Display Components ========== */

/* Common Styles - using :deep() for dynamic components */
:deep(.stat-row) {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

:deep(.stat-box) {
  flex: 1;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  padding: 10px 8px;
  text-align: center;
}

:deep(.stat-box .stat-num) {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-background);
  font-family: 'JetBrains Mono', monospace;
}

:deep(.stat-box .stat-label) {
  display: block;
  font-size: 10px;
  color: var(--color-disabled);
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

:deep(.stat-box.highlight) {
  background: var(--color-success-bg);
  border-color: var(--color-success);
}

:deep(.stat-box.highlight .stat-num) {
  color: var(--color-success);
}

:deep(.stat-box.muted) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
}

:deep(.stat-box.muted .stat-num) {
  color: var(--color-muted);
}

:deep(.query-display) {
  background: var(--color-surface-container-low);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--color-on-surface);
  margin-bottom: 12px;
  border: 1px solid var(--color-outline);
  line-height: 1.5;
}

:deep(.expand-details) {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.expand-details:hover) {
  border-color: var(--color-outline);
  color: var(--color-on-surface);
}

:deep(.detail-content) {
  margin-top: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  padding: 14px;
}

:deep(.section-label) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-surface-container-low);
}

/* Facts Section */
:deep(.facts-section) {
  margin-bottom: 14px;
}

:deep(.fact-row) {
  display: flex;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-surface-container-low);
}

:deep(.fact-row:last-child) {
  border-bottom: none;
}

:deep(.fact-row.active) {
  background: var(--color-success-bg);
  margin: 0 -10px;
  padding: 8px 10px;
  border-radius: 6px;
  border-bottom: none;
}

:deep(.fact-idx) {
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-container-low);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-muted);
  flex-shrink: 0;
}

:deep(.fact-row.active .fact-idx) {
  background: var(--color-success);
  color: var(--color-success);
}

:deep(.fact-text) {
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.6;
}

/* Entities Section */
:deep(.entities-section) {
  margin-bottom: 14px;
}

:deep(.entity-chips) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.entity-chip) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  padding: 6px 12px;
}

:deep(.chip-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-background);
}

:deep(.chip-type) {
  font-size: 10px;
  color: var(--color-disabled);
  background: var(--color-outline);
  padding: 1px 6px;
  border-radius: 3px;
}

/* Relations Section */
:deep(.relations-section) {
  margin-bottom: 14px;
}

:deep(.relation-row) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--color-surface-container-low);
}

:deep(.relation-row:last-child) {
  border-bottom: none;
}

:deep(.rel-node) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-background);
  background: var(--color-surface-container-low);
  padding: 4px 10px;
  border-radius: 4px;
}

:deep(.rel-edge) {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-surface);
  background: var(--color-info);
  padding: 3px 10px;
  border-radius: 10px;
}

/* ========== Interview Display - Conversation Style ========== */
:deep(.interview-display) {
  padding: 0;
}

/* Header */
:deep(.interview-display .interview-header) {
  padding: 0;
  background: transparent;
  border-bottom: none;
  margin-bottom: 16px;
}

:deep(.interview-display .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.interview-display .header-title) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-background);
  letter-spacing: -0.01em;
}

:deep(.interview-display .header-stats) {
  display: flex;
  align-items: center;
  gap: 6px;
}

:deep(.interview-display .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

:deep(.interview-display .stat-value) {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-info);
  font-family: 'JetBrains Mono', monospace;
}

:deep(.interview-display .stat-label) {
  font-size: 11px;
  color: var(--color-disabled);
  text-transform: lowercase;
}

:deep(.interview-display .stat-divider) {
  color: var(--color-outline);
  font-size: 12px;
}

:deep(.interview-display .stat-size) {
  font-size: 11px;
  color: var(--color-disabled);
  font-family: 'JetBrains Mono', monospace;
}

:deep(.interview-display .header-topic) {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.5;
}

/* Agent Tabs - Card Style */
:deep(.interview-display .agent-tabs) {
  display: flex;
  gap: 8px;
  padding: 0 0 14px 0;
  background: transparent;
  border-bottom: 1px solid var(--color-surface-container-low);
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--color-outline) transparent;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar) {
  height: 4px;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-thumb) {
  background: var(--color-outline);
  border-radius: 2px;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-thumb:hover) {
  background: var(--color-outline);
}

:deep(.interview-display .agent-tab) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

:deep(.interview-display .agent-tab:hover) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
  color: var(--color-on-surface);
}

:deep(.interview-display .agent-tab.active) {
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
  border-color: #A5B4FC;
  color: #4338CA;
  box-shadow: 0 1px 2px rgba(99, 102, 241, 0.1);
}

:deep(.interview-display .tab-avatar) {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}

:deep(.interview-display .agent-tab:hover .tab-avatar) {
  background: var(--color-outline);
}

:deep(.interview-display .agent-tab.active .tab-avatar) {
  background: var(--color-info);
  color: var(--color-surface);
}

:deep(.interview-display .tab-name) {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Interview Detail */
:deep(.interview-display .interview-detail) {
  padding: 12px 0;
  background: transparent;
}

/* Agent Profile - No card */
:deep(.interview-display .agent-profile) {
  display: flex;
  gap: 12px;
  padding: 0;
  background: transparent;
  border: none;
  margin-bottom: 16px;
}

:deep(.interview-display .profile-avatar) {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  color: var(--color-muted);
  font-size: 14px;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

:deep(.interview-display .profile-info) {
  flex: 1;
  min-width: 0;
}

:deep(.interview-display .profile-name) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-background);
  margin-bottom: 2px;
}

:deep(.interview-display .profile-role) {
  font-size: 11px;
  color: var(--color-muted);
  margin-bottom: 4px;
}

:deep(.interview-display .profile-bio) {
  font-size: 11px;
  color: var(--color-disabled);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Selection Reason - Fundamentar a decisão */
:deep(.interview-display .selection-reason) {
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

:deep(.interview-display .reason-label) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 6px;
}

:deep(.interview-display .reason-content) {
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.6;
}

/* Q&A Thread - Clean list */
:deep(.interview-display .qa-thread) {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

:deep(.interview-display .qa-pair) {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

:deep(.interview-display .qa-question),
:deep(.interview-display .qa-answer) {
  display: flex;
  gap: 12px;
}

:deep(.interview-display .qa-badge) {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
  flex-shrink: 0;
}

:deep(.interview-display .q-badge) {
  background: transparent;
  color: var(--color-disabled);
  border: 1px solid var(--color-outline);
}

:deep(.interview-display .a-badge) {
  background: var(--color-info);
  color: var(--color-surface);
  border: 1px solid var(--color-info);
}

:deep(.interview-display .qa-content) {
  flex: 1;
  min-width: 0;
}

:deep(.interview-display .qa-sender) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-disabled);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

:deep(.interview-display .qa-text) {
  font-size: 13px;
  color: var(--color-on-surface);
  line-height: 1.6;
}

:deep(.interview-display .qa-answer) {
  background: transparent;
  padding: 0;
  border: none;
  margin-top: 0;
}

:deep(.interview-display .answer-placeholder) {
  opacity: 0.6;
}

:deep(.interview-display .placeholder-text) {
  font-style: italic;
  color: var(--color-disabled);
}

:deep(.interview-display .qa-answer-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

/* Platform Switch */
:deep(.interview-display .platform-switch) {
  display: flex;
  gap: 2px;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

:deep(.interview-display .platform-btn) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-disabled);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.interview-display .platform-btn:hover) {
  color: var(--color-muted);
}

:deep(.interview-display .platform-btn.active) {
  background: transparent;
  color: var(--color-info);
  border-color: var(--color-outline);
  box-shadow: none;
}

:deep(.interview-display .platform-icon) {
  flex-shrink: 0;
}

:deep(.interview-display .answer-text) {
  font-size: 13px;
  color: var(--color-on-background);
  line-height: 1.6;
}

:deep(.interview-display .answer-text strong) {
  color: var(--color-on-background);
  font-weight: 600;
}

:deep(.interview-display .expand-answer-btn) {
  display: inline-block;
  margin-top: 8px;
  padding: 0;
  background: transparent;
  border: none;
  border-bottom: 1px dotted var(--color-outline);
  border-radius: 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-disabled);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.interview-display .expand-answer-btn:hover) {
  background: transparent;
  color: var(--color-muted);
  border-bottom-style: solid;
}

/* Quotes Section - Clean list */
:deep(.interview-display .quotes-section) {
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-surface-container-low);
  border-radius: 0;
  padding: 16px 0 0 0;
  margin-top: 16px;
}

:deep(.interview-display .quotes-header) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-disabled);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
}

:deep(.interview-display .quotes-list) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.interview-display .quote-item) {
  margin: 0;
  padding: 10px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  font-size: 12px;
  font-style: italic;
  color: var(--color-muted);
  line-height: 1.5;
}

/* Summary Section */
:deep(.interview-display .summary-section) {
  margin-top: 20px;
  padding: 16px 0 0 0;
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-surface-container-low);
  border-radius: 0;
}

:deep(.interview-display .summary-header) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-disabled);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

:deep(.interview-display .summary-content) {
  font-size: 13px;
  color: var(--color-on-surface);
  line-height: 1.6;
}

/* Markdown styles in summary */
:deep(.interview-display .summary-content h2),
:deep(.interview-display .summary-content h3),
:deep(.interview-display .summary-content h4),
:deep(.interview-display .summary-content h5) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  color: var(--color-on-background);
}

:deep(.interview-display .summary-content h2) {
  font-size: 15px;
}

:deep(.interview-display .summary-content h3) {
  font-size: 14px;
}

:deep(.interview-display .summary-content h4),
:deep(.interview-display .summary-content h5) {
  font-size: 13px;
}

:deep(.interview-display .summary-content p) {
  margin: 8px 0;
}

:deep(.interview-display .summary-content strong) {
  font-weight: 600;
  color: var(--color-on-background);
}

:deep(.interview-display .summary-content em) {
  font-style: italic;
}

:deep(.interview-display .summary-content ul),
:deep(.interview-display .summary-content ol) {
  margin: 8px 0;
  padding-left: 20px;
}

:deep(.interview-display .summary-content li) {
  margin: 4px 0;
}

:deep(.interview-display .summary-content blockquote) {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 3px solid var(--color-outline);
  color: var(--color-muted);
  font-style: italic;
}

/* Markdown styles in quotes */
:deep(.interview-display .quote-item strong) {
  font-weight: 600;
  color: var(--color-on-surface);
}

:deep(.interview-display .quote-item em) {
  font-style: italic;
}

/* ========== Enhanced Insight Display Styles ========== */
:deep(.insight-display) {
  padding: 0;
}

:deep(.insight-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-info-bg);
  border-bottom: none;
}

:deep(.insight-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.insight-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-info);
}

:deep(.insight-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.insight-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.insight-header .stat-value) {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--color-info);
}

:deep(.insight-header .stat-label) {
  color: var(--color-info);
  font-size: 10px;
}

:deep(.insight-header .stat-divider) {
  color: var(--color-info-bg);
  margin: 0 4px;
}

:deep(.insight-header .stat-size) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.insight-header .header-topic) {
  font-size: 13px;
  color: #5B21B6;
  line-height: 1.5;
}

:deep(.insight-header .header-scenario) {
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-info);
}

:deep(.insight-header .scenario-label) {
  font-weight: 600;
}

:deep(.insight-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-top: none;
}

:deep(.insight-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.insight-tab:hover) {
  background: var(--color-surface-container-low);
  color: var(--color-on-surface);
}

:deep(.insight-tab.active) {
  background: var(--color-surface);
  color: var(--color-info);
  border-color: #C4B5FD;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}


:deep(.insight-content) {
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

:deep(.insight-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-surface-container-low);
}

:deep(.insight-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
}

:deep(.insight-display .panel-count) {
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.insight-display .facts-list),
:deep(.insight-display .relations-list),
:deep(.insight-display .subqueries-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.insight-display .entities-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.insight-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.insight-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  border-radius: 50%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-muted);
}

:deep(.insight-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-on-surface);
  line-height: 1.6;
}

/* Entity Tag Styles - Compact multi-column layout */
:deep(.insight-display .entity-tag) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  cursor: default;
  transition: all 0.15s ease;
}

:deep(.insight-display .entity-tag:hover) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
}

:deep(.insight-display .entity-tag .entity-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-background);
}

:deep(.insight-display .entity-tag .entity-type) {
  font-size: 9px;
  color: var(--color-info);
  background: var(--color-info-bg);
  padding: 1px 4px;
  border-radius: 3px;
}

:deep(.insight-display .entity-tag .entity-fact-count) {
  font-size: 9px;
  color: var(--color-disabled);
  margin-left: 2px;
}

/* Legacy entity card styles for backwards compatibility */
:deep(.insight-display .entity-card) {
  padding: 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 8px;
}

:deep(.insight-display .entity-header) {
  display: flex;
  align-items: center;
  gap: 10px;
}

:deep(.insight-display .entity-info) {
  flex: 1;
}

:deep(.insight-display .entity-card .entity-name) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-background);
}

:deep(.insight-display .entity-card .entity-type) {
  font-size: 10px;
  color: var(--color-info);
  background: var(--color-info-bg);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 2px;
}

:deep(.insight-display .entity-card .entity-fact-count) {
  font-size: 10px;
  color: var(--color-disabled);
  background: var(--color-surface-container-low);
  padding: 2px 6px;
  border-radius: 4px;
}

:deep(.insight-display .entity-summary) {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-outline);
  font-size: 11px;
  color: var(--color-muted);
  line-height: 1.5;
}

/* Relation Item Styles */
:deep(.insight-display .relation-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.insight-display .rel-source),
:deep(.insight-display .rel-target) {
  padding: 4px 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-on-surface);
}

:deep(.insight-display .rel-arrow) {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

:deep(.insight-display .rel-line) {
  flex: 1;
  height: 1px;
  background: var(--color-outline);
}

:deep(.insight-display .rel-label) {
  padding: 2px 6px;
  background: var(--color-info-bg);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-info);
  white-space: nowrap;
}

/* Sub-query Styles */
:deep(.insight-display .subquery-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.insight-display .subquery-number) {
  flex-shrink: 0;
  padding: 2px 6px;
  background: var(--color-info);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-surface);
}

:deep(.insight-display .subquery-text) {
  font-size: 12px;
  color: var(--color-on-surface);
  line-height: 1.5;
}

/* Expand Button */
:deep(.insight-display .expand-btn),
:deep(.panorama-display .expand-btn),
:deep(.quick-search-display .expand-btn) {
  display: block;
  width: 100%;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 0px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

:deep(.insight-display .expand-btn:hover),
:deep(.panorama-display .expand-btn:hover),
:deep(.quick-search-display .expand-btn:hover) {
  background: var(--color-surface-container-low);
  color: var(--color-on-surface);
  border-color: var(--color-outline);
}

/* Empty State */
:deep(.insight-display .empty-state),
:deep(.panorama-display .empty-state),
:deep(.quick-search-display .empty-state) {
  padding: 24px;
  text-align: center;
  font-size: 12px;
  color: var(--color-disabled);
}

/* ========== Enhanced Panorama Display Styles ========== */
:deep(.panorama-display) {
  padding: 0;
}

:deep(.panorama-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-info);
  border-bottom: none;
}

:deep(.panorama-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.panorama-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-info);
}

:deep(.panorama-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.panorama-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.panorama-header .stat-value) {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--color-info);
}

:deep(.panorama-header .stat-label) {
  color: #60A5FA;
  font-size: 10px;
}

:deep(.panorama-header .stat-divider) {
  color: var(--color-info);
  margin: 0 4px;
}

:deep(.panorama-header .stat-size) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.panorama-header .header-topic) {
  font-size: 13px;
  color: #1E40AF;
  line-height: 1.5;
}

:deep(.panorama-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-top: none;
}

:deep(.panorama-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.panorama-tab:hover) {
  background: var(--color-surface-container-low);
  color: var(--color-on-surface);
}

:deep(.panorama-tab.active) {
  background: var(--color-surface);
  color: var(--color-info);
  border-color: #93C5FD;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}


:deep(.panorama-content) {
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

:deep(.panorama-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-surface-container-low);
}

:deep(.panorama-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
}

:deep(.panorama-display .panel-count) {
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.panorama-display .facts-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.panorama-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.panorama-display .fact-item.active) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
}

:deep(.panorama-display .fact-item.historical) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
}

:deep(.panorama-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  border-radius: 50%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-muted);
}

:deep(.panorama-display .fact-item.active .fact-number) {
  background: var(--color-outline);
  color: var(--color-muted);
}

:deep(.panorama-display .fact-item.historical .fact-number) {
  background: var(--color-disabled);
  color: var(--color-surface);
}

:deep(.panorama-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-on-surface);
  line-height: 1.6;
}

:deep(.panorama-display .fact-time) {
  display: block;
  font-size: 10px;
  color: var(--color-disabled);
  margin-bottom: 4px;
  font-family: 'JetBrains Mono', monospace;
}

:deep(.panorama-display .fact-text) {
  display: block;
}

/* Entities Grid */
:deep(.panorama-display .entities-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.panorama-display .entity-tag) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.panorama-display .entity-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-surface);
}

:deep(.panorama-display .entity-type) {
  font-size: 10px;
  color: var(--color-info);
  background: var(--color-info-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* ========== Enhanced Quick Search Display Styles ========== */
:deep(.quick-search-display) {
  padding: 0;
}

:deep(.quicksearch-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-warning);
  border-bottom: none;
}

:deep(.quicksearch-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.quicksearch-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-warning);
}

:deep(.quicksearch-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.quicksearch-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.quicksearch-header .stat-value) {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--color-warning);
}

:deep(.quicksearch-header .stat-label) {
  color: #FB923C;
  font-size: 10px;
}

:deep(.quicksearch-header .stat-divider) {
  color: var(--color-warning);
  margin: 0 4px;
}

:deep(.quicksearch-header .stat-size) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.quicksearch-header .header-query) {
  font-size: 13px;
  color: #9A3412;
  line-height: 1.5;
}

:deep(.quicksearch-header .query-label) {
  font-weight: 600;
}

:deep(.quicksearch-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-top: none;
}

:deep(.quicksearch-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.quicksearch-tab:hover) {
  background: var(--color-surface-container-low);
  color: var(--color-on-surface);
}

:deep(.quicksearch-tab.active) {
  background: var(--color-surface);
  color: var(--color-warning);
  border-color: #FDBA74;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}


:deep(.quicksearch-content) {
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

/* When there are no tabs, content connects directly to header */
:deep(.quicksearch-content.no-tabs) {
  border-top: none;
}

:deep(.quick-search-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-surface-container-low);
}

:deep(.quick-search-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
}

:deep(.quick-search-display .panel-count) {
  font-size: 10px;
  color: var(--color-disabled);
}

:deep(.quick-search-display .facts-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.quick-search-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.quick-search-display .fact-item.active) {
  background: var(--color-surface-container-low);
  border-color: var(--color-outline);
}

:deep(.quick-search-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-outline);
  border-radius: 50%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-muted);
}

:deep(.quick-search-display .fact-item.active .fact-number) {
  background: var(--color-outline);
  color: var(--color-muted);
}

:deep(.quick-search-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-on-surface);
  line-height: 1.6;
}

/* Edges Panel */
:deep(.quick-search-display .edges-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.quick-search-display .edge-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.quick-search-display .edge-source),
:deep(.quick-search-display .edge-target) {
  padding: 4px 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-on-surface);
}

:deep(.quick-search-display .edge-arrow) {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

:deep(.quick-search-display .edge-line) {
  flex: 1;
  height: 1px;
  background: var(--color-outline);
}

:deep(.quick-search-display .edge-label) {
  padding: 2px 6px;
  background: var(--color-warning-bg);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-warning);
  white-space: nowrap;
}

/* Nodes Grid */
:deep(.quick-search-display .nodes-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.quick-search-display .node-tag) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
}

:deep(.quick-search-display .node-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-surface);
}

:deep(.quick-search-display .node-type) {
  font-size: 10px;
  color: var(--color-warning);
  background: var(--color-warning-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Console Logs - Keep Flow Layout Similar Copy Logic Styles Code Sync Standard Component Structure Templates Components Flow Structure Logic Component Architecture Copy Styles Setup Base Vue Flow Pattern Architecture Process Control Components Render Engine Sync App Style Guide Component State Setup Action Call Method UI View Flow Sync Data Components Update Method Target Prop */
.console-logs {
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

.log-title {
  text-transform: uppercase;
  letter-spacing: 0.1em;
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
  line-height: 1.5;
}

.log-msg {
  color: var(--color-disabled);
  word-break: break-all;
}

.log-msg.error { color: #EF5350; }
.log-msg.warning { color: #FFA726; }
.log-msg.success { color: #66BB6A; }

/* Contamination Warning Styles */
.contamination-warning {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  border: 1px solid #F59E0B;
  border-radius: 8px;
  margin-top: 8px;
}

.contamination-warning .warning-icon {
  flex-shrink: 0;
  color: var(--color-warning);
  display: flex;
  align-items: center;
}

.contamination-warning .warning-text {
  font-size: 13px;
  color: #92400E;
  font-weight: 500;
}

/* Report tables */
.report-table {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
  overflow-x: auto;
  display: block;
}

.report-table thead {
  background: var(--color-surface-container-low);
  border-bottom: 2px solid var(--color-outline);
}

.report-table th,
.report-table td {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  border-bottom: 1px solid var(--color-outline);
}

.report-table th {
  font-family: var(--font-machine);
  font-weight: var(--font-weight-bold);
  color: var(--color-on-background);
}

.report-table tbody tr:hover {
  background: var(--color-surface-container-low);
}

/* Data source tags */
.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: var(--text-xs);
  font-family: var(--font-machine);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  line-height: 1.4;
  white-space: nowrap;
  vertical-align: middle;
}

.source-realizado {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.source-consenso {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.source-projecao {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.source-simulacao {
  background: var(--color-error-bg);
  color: var(--color-error);
}
</style>

<style>
/* English locale: smaller report title */
html[lang="en"] .report-header-block .main-title {
  font-size: 28px;
}
</style>
e>

e>

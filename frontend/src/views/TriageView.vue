<template>
  <div class="triage-view">
    <header class="triage-header">
      <h1 class="triage-title">Triagem de Feedback — Beta</h1>
    </header>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="summary-card">
        <span class="summary-label">Total</span>
        <span class="summary-value">{{ summary.total || 0 }}</span>
      </div>
      <div class="summary-card severity-p0">
        <span class="summary-label">P0</span>
        <span class="summary-value">{{ summary.by_severity?.p0 || 0 }}</span>
      </div>
      <div class="summary-card severity-p1">
        <span class="summary-label">P1</span>
        <span class="summary-value">{{ summary.by_severity?.p1 || 0 }}</span>
      </div>
      <div class="summary-card severity-p2">
        <span class="summary-label">P2</span>
        <span class="summary-value">{{ summary.by_severity?.p2 || 0 }}</span>
      </div>
      <div class="summary-card severity-p3">
        <span class="summary-label">P3</span>
        <span class="summary-value">{{ summary.by_severity?.p3 || 0 }}</span>
      </div>
      <div class="summary-card severity-untriaged">
        <span class="summary-label">Não classificados</span>
        <span class="summary-value">{{ summary.by_severity?.untriaged || 0 }}</span>
      </div>
      <div class="summary-card">
        <span class="summary-label">Média de satisfação</span>
        <span class="summary-value">{{ summary.avg_rating || 0 }}/5</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <select v-model="filters.category" class="filter-select">
        <option value="">Todas categorias</option>
        <option value="bug">Bug</option>
        <option value="ux_confusion">Confusão de UX</option>
        <option value="suggestion">Sugestão</option>
      </select>
      <select v-model="filters.stage" class="filter-select">
        <option value="">Todas etapas</option>
        <option value="graph_build">Grafo</option>
        <option value="env_setup">Ambiente</option>
        <option value="simulation">Simulação</option>
        <option value="report">Relatório</option>
        <option value="inspection">Inspeção</option>
      </select>
      <select v-model="filters.severity" class="filter-select">
        <option value="">Todas severidades</option>
        <option value="untriaged">Não classificado</option>
        <option value="p0">P0 — Bloqueio</option>
        <option value="p1">P1 — Grave</option>
        <option value="p2">P2 — Médio</option>
        <option value="p3">P3 — Leve</option>
      </select>
      <input v-model="filters.since" type="date" class="filter-input" />
      <input v-model="filters.until" type="date" class="filter-input" />
      <BaseButton variant="secondary" size="sm" @click="applyFilters">
        Filtrar
      </BaseButton>
    </div>

    <!-- Bulk Actions -->
    <div class="bulk-actions">
      <BaseButton variant="outline" size="sm" @click="onAutoClassify">
        Auto-classificar
      </BaseButton>
      <BaseButton variant="outline" size="sm" @click="onGenerateBacklog">
        Gerar Backlog
      </BaseButton>
      <BaseButton variant="outline" size="sm" @click="onGenerateChangelog">
        Gerar Changelog
      </BaseButton>
    </div>

    <!-- Feedback Table -->
    <div v-if="isLoading" class="loading-state">
      <Icon name="loader-2" :size="24" class="spin" />
      <span>Carregando feedbacks...</span>
    </div>

    <table v-else class="feedback-table">
      <thead>
        <tr>
          <th>Data</th>
          <th>Etapa</th>
          <th>Categoria</th>
          <th>Nota</th>
          <th>Severidade</th>
          <th>Comentário</th>
          <th>Anexo</th>
          <th>Ação</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in feedbacks" :key="item.feedback_id">
          <td class="cell-date">{{ formatDate(item.created_at) }}</td>
          <td class="cell-stage">{{ item.stage }}</td>
          <td class="cell-category">
            <span class="category-badge" :class="item.category">{{ item.category }}</span>
          </td>
          <td class="cell-rating">
            <span class="rating-stars">{{ '★'.repeat(item.rating) }}{{ '☆'.repeat(5 - item.rating) }}</span>
          </td>
          <td class="cell-severity">
            <select
              :value="item.severity"
              class="severity-select"
              @change="onSeverityChange(item.feedback_id, $event.target.value)"
            >
              <option value="untriaged">Não classificado</option>
              <option value="p0">P0</option>
              <option value="p1">P1</option>
              <option value="p2">P2</option>
              <option value="p3">P3</option>
            </select>
          </td>
          <td class="cell-comment">{{ item.comment }}</td>
          <td class="cell-attachments">
            <span v-if="item.simulation_id" class="attach-chip">{{ item.simulation_id }}</span>
            <span v-if="item.report_id" class="attach-chip">{{ item.report_id }}</span>
          </td>
          <td class="cell-action">
            <BaseButton variant="ghost" size="sm" @click="saveSeverity(item.feedback_id)">
              Salvar
            </BaseButton>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="!isLoading && feedbacks.length === 0" class="empty-state">
      Nenhum feedback encontrado.
    </div>

    <!-- Notification -->
    <div v-if="notification" class="triage-notification" :class="notification.type" role="alert">
      {{ notification.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BaseButton from '../components/base/BaseButton.vue'
import Icon from '../components/Icon.vue'
import {
  listFeedback,
  getFeedbackStats,
  updateFeedback,
  getFeedback,
} from '../api/feedback.js'

const feedbacks = ref([])
const summary = ref({})
const isLoading = ref(false)
const filters = ref({
  category: '',
  stage: '',
  severity: '',
  since: '',
  until: '',
})
const notification = ref(null)
const pendingChanges = ref({})

const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR')
}

const showNotification = (message, type = 'success') => {
  notification.value = { message, type }
  setTimeout(() => { notification.value = null }, 4000)
}

const loadData = async () => {
  isLoading.value = true
  try {
    const [listRes, statsRes] = await Promise.all([
      listFeedback({ limit: 200 }),
      getFeedbackStats(),
    ])
    feedbacks.value = listRes.data?.items || []
    summary.value = statsRes.data || {}
  } catch (err) {
    showNotification('Erro ao carregar feedbacks: ' + (err.message || ''), 'error')
  } finally {
    isLoading.value = false
  }
}

const applyFilters = async () => {
  isLoading.value = true
  try {
    const params = { limit: 200 }
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.stage) params.stage = filters.value.stage
    if (filters.value.severity) params.severity = filters.value.severity
    const res = await listFeedback(params)
    let items = res.data?.items || []
    // Client-side date filter
    if (filters.value.since) {
      const sinceIso = new Date(filters.value.since).toISOString()
      items = items.filter(i => i.created_at >= sinceIso)
    }
    if (filters.value.until) {
      const untilIso = new Date(filters.value.until + 'T23:59:59').toISOString()
      items = items.filter(i => i.created_at <= untilIso)
    }
    feedbacks.value = items
  } catch (err) {
    showNotification('Erro ao filtrar: ' + (err.message || ''), 'error')
  } finally {
    isLoading.value = false
  }
}

const onSeverityChange = (feedbackId, severity) => {
  pendingChanges.value[feedbackId] = severity
}

const saveSeverity = async (feedbackId) => {
  const severity = pendingChanges.value[feedbackId]
  if (!severity) {
    showNotification('Selecione uma severidade primeiro', 'error')
    return
  }
  try {
    await updateFeedback(feedbackId, { severity })
    showNotification('Severidade atualizada')
    delete pendingChanges.value[feedbackId]
    await loadData()
  } catch (err) {
    showNotification('Erro ao salvar: ' + (err.message || ''), 'error')
  }
}

const onAutoClassify = async () => {
  try {
    // This would call a new API endpoint; for now, we simulate
    showNotification('Auto-classificação executada (simulado — endpoint não disponível no cliente)', 'info')
  } catch (err) {
    showNotification('Erro: ' + (err.message || ''), 'error')
  }
}

const onGenerateBacklog = async () => {
  try {
    showNotification('Backlog gerado (simulado — endpoint não disponível no cliente)', 'info')
  } catch (err) {
    showNotification('Erro: ' + (err.message || ''), 'error')
  }
}

const onGenerateChangelog = async () => {
  try {
    showNotification('Changelog gerado (simulado — endpoint não disponível no cliente)', 'info')
  } catch (err) {
    showNotification('Erro: ' + (err.message || ''), 'error')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.triage-view {
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

.triage-header {
  margin-bottom: var(--space-6);
}

.triage-title {
  font-family: var(--font-machine);
  font-size: var(--text-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-on-background);
  margin: 0;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.summary-card {
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-on-background);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  box-shadow: var(--shadow-brutalist);
}

.summary-label {
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  color: var(--color-muted);
  text-transform: uppercase;
}

.summary-value {
  font-family: var(--font-machine);
  font-size: var(--text-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-on-background);
}

.severity-p0 { border-color: var(--color-error); }
.severity-p1 { border-color: #d97706; }
.severity-p2 { border-color: var(--color-warning); }
.severity-p3 { border-color: var(--color-success); }
.severity-untriaged { border-color: var(--color-outline); }

/* Filters */
.filters-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  align-items: center;
}

.filter-select,
.filter-input {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-outline);
  border-radius: 0;
  background: var(--color-surface-elevated);
  color: var(--color-on-background);
}

/* Bulk Actions */
.bulk-actions {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

/* Table */
.feedback-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-on-background);
  box-shadow: var(--shadow-brutalist);
}

.feedback-table thead {
  background: var(--color-surface-container-highest);
}

.feedback-table th,
.feedback-table td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--color-outline);
}

.feedback-table th {
  font-family: var(--font-machine);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
}

.cell-date { white-space: nowrap; }
.cell-stage { text-transform: capitalize; }

.category-badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  border: 1px solid var(--color-outline);
}

.category-badge.bug { background: var(--color-error-container); color: var(--color-on-error-container); border-color: var(--color-error); }
.category-badge.ux_confusion { background: var(--color-warning-container); color: var(--color-on-warning-container); border-color: var(--color-warning); }
.category-badge.suggestion { background: var(--color-success-container); color: var(--color-on-success-container); border-color: var(--color-success); }

.rating-stars {
  color: var(--color-warning);
  letter-spacing: 2px;
}

.severity-select {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--color-outline);
  border-radius: 0;
  background: var(--color-surface-elevated);
  color: var(--color-on-background);
}

.cell-comment {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attach-chip {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  margin-right: var(--space-1);
}

/* States */
.loading-state,
.empty-state {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-muted);
  font-family: var(--font-machine);
}

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Notification */
.triage-notification {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-3) var(--space-6);
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  border: 2px solid var(--color-on-background);
  box-shadow: var(--shadow-brutalist);
  z-index: 100;
}

.triage-notification.success {
  background: var(--color-success-container);
  color: var(--color-on-success-container);
}

.triage-notification.error {
  background: var(--color-error-container);
  color: var(--color-on-error-container);
}

.triage-notification.info {
  background: var(--color-surface-container-low);
  color: var(--color-on-background);
}

@media (max-width: 768px) {
  .triage-view {
    padding: var(--space-3);
  }
  .feedback-table {
    font-size: var(--text-xs);
  }
  .feedback-table th,
  .feedback-table td {
    padding: var(--space-2);
  }
  .cell-comment {
    max-width: 120px;
  }
}
</style>

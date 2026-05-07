<template>
  <div class="sim-confirm-modal" role="dialog" aria-modal="true" :aria-label="uiLabels.title">
    <div class="sim-confirm-modal__overlay" @click.self="onCancel"></div>
    <div class="sim-confirm-modal__panel">
      <div class="sim-confirm-modal__header">
        <h3 class="sim-confirm-modal__title">{{ uiLabels.title }}</h3>
        <p class="sim-confirm-modal__subtitle">{{ uiLabels.subtitle }}</p>
      </div>

      <div class="sim-confirm-modal__body">
        <div class="confirm-summary">
          <div class="confirm-row">
            <span class="confirm-label">{{ uiLabels.simulationId }}</span>
            <span class="confirm-value mono">{{ simulationId || '-' }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">{{ uiLabels.project }}</span>
            <span class="confirm-value">{{ projectName || '-' }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">{{ uiLabels.maxRounds }}</span>
            <span class="confirm-value">{{ maxRounds || uiLabels.auto }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">{{ uiLabels.minutesPerRound }}</span>
            <span class="confirm-value">{{ minutesPerRound }}min</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">{{ uiLabels.platforms }}</span>
            <span class="confirm-value">Twitter + Reddit</span>
          </div>
        </div>

        <div class="evolution-config">
          <div class="evolution-toggle">
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="localEnableEvolution"
                class="toggle-input"
              />
              <span class="toggle-slider"></span>
              <span class="toggle-text">{{ uiLabels.enableEvolution }}</span>
            </label>
          </div>
          <div v-if="localEnableEvolution" class="evolution-preset">
            <label class="preset-label">{{ uiLabels.evolutionPreset }}</label>
            <select v-model="localPreset" class="preset-select">
              <option value="stable">{{ uiLabels.presetStable }}</option>
              <option value="sensitive">{{ uiLabels.presetSensitive }}</option>
              <option value="polarizable">{{ uiLabels.presetPolarizable }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="sim-confirm-modal__actions">
        <button class="action-btn secondary" @click="onCancel">
          {{ uiLabels.cancel }}
        </button>
        <button class="action-btn primary" @click="onConfirm">
          {{ uiLabels.start }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  simulationId: { type: String, default: '' },
  projectName: { type: String, default: '' },
  maxRounds: { type: Number, default: null },
  minutesPerRound: { type: Number, default: 30 },
  enableAgentEvolution: { type: Boolean, default: true },
  agentEvolutionPreset: { type: String, default: 'stable' },
})

const emit = defineEmits(['confirm', 'cancel'])

const localEnableEvolution = ref(props.enableAgentEvolution)
const localPreset = ref(props.agentEvolutionPreset)

const uiLabels = {
  title: 'Confirmar Início da Simulação',
  subtitle: 'Revise os parâmetros antes de iniciar o motor de simulação.',
  simulationId: 'ID da Simulação',
  project: 'Projeto',
  maxRounds: 'Máximo de Turnos',
  minutesPerRound: 'Minutos por Turno',
  platforms: 'Plataformas',
  auto: 'Automático (LLM)',
  cancel: 'Voltar para Step 2',
  start: 'Iniciar Simulação',
  enableEvolution: 'Ativar Evolução de Agentes',
  evolutionPreset: 'Preset de Evolução',
  presetStable: 'Estável',
  presetSensitive: 'Sensível',
  presetPolarizable: 'Polarizável',
}

const onConfirm = () => emit('confirm', {
  enableAgentEvolution: localEnableEvolution.value,
  agentEvolutionPreset: localPreset.value,
})
const onCancel = () => emit('cancel')
</script>

<style scoped>
.sim-confirm-modal {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sim-confirm-modal__overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.sim-confirm-modal__panel {
  position: relative;
  background: var(--color-surface);
  border-radius: var(--radius-lg, 8px);
  padding: var(--space-6, 24px);
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: var(--space-5, 20px);
}

.sim-confirm-modal__header {
  text-align: center;
}

.sim-confirm-modal__title {
  margin: 0 0 var(--space-1, 4px);
  font-size: var(--text-lg, 18px);
  font-weight: var(--font-weight-semibold, 600);
}

.sim-confirm-modal__subtitle {
  margin: 0;
  font-size: var(--text-sm, 14px);
  color: var(--color-text-muted, #6b7280);
}

.confirm-summary {
  display: flex;
  flex-direction: column;
  gap: var(--space-3, 12px);
}

.confirm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2, 8px) var(--space-3, 12px);
  background: var(--color-surface-container-low);
  border-radius: var(--radius-md, 6px);
}

.confirm-label {
  font-size: var(--text-sm, 14px);
  color: var(--color-text-muted, #6b7280);
}

.confirm-value {
  font-size: var(--text-sm, 14px);
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-on-background);
}

.sim-confirm-modal__actions {
  display: flex;
  gap: var(--space-3, 12px);
}

.action-btn {
  flex: 1;
  padding: var(--space-3, 12px);
  font-size: var(--text-sm, 14px);
  font-weight: var(--font-weight-semibold, 600);
  border-radius: var(--radius-md, 6px);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.action-btn.secondary {
  background: var(--color-surface-container-highest);
  color: var(--color-on-background);
  border-color: var(--color-outline);
}

.action-btn.primary {
  background: var(--color-on-background);
  color: var(--color-surface);
}

.evolution-config {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-outline);
}

.evolution-toggle {
  margin-bottom: 12px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-on-background);
}

.toggle-input {
  display: none;
}

.toggle-slider {
  width: 40px;
  height: 22px;
  background: var(--color-surface-container-highest);
  border-radius: 11px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-input:checked + .toggle-slider {
  background: var(--color-primary);
}

.toggle-input:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.evolution-preset {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preset-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.preset-select {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-background);
  font-size: 14px;
  cursor: pointer;
}
</style>

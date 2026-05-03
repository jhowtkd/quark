<template>
  <div v-if="isVisible" class="beta-feedback-wrapper">
    <!-- Loading State -->
    <div v-if="isLoading" class="feedback-loading">
      <div class="loading-spinner"></div>
      <span>Enviando feedback...</span>
    </div>

    <!-- Success State -->
    <div v-else-if="isSuccess" class="feedback-success">
      <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <h3>Obrigado pelo seu feedback!</h3>
      <p>Sua avaliação foi recebida e ajudará a melhorar a plataforma.</p>
    </div>

    <!-- Form State -->
    <form v-else class="beta-feedback-form" @submit.prevent="handleSubmit">
      <div class="feedback-header">
        <h3 class="feedback-title">Feedback Beta</h3>
        <p class="feedback-subtitle">Avalie cada etapa do pipeline (1–5 estrelas)</p>
      </div>

      <div class="ratings-section">
        <div v-for="stage in stages" :key="stage.key" class="rating-group">
          <span class="rating-label">{{ stage.label }}</span>
          <div class="stars" role="radiogroup" :aria-label="`Avaliação para ${stage.label}`">
            <button
              v-for="n in 5"
              :key="n"
              type="button"
              class="star-btn"
              :class="{ filled: n <= ratings[stage.key], hovered: n <= hoveredStar[stage.key] }"
              :aria-checked="n === ratings[stage.key]"
              role="radio"
              @mouseenter="hoveredStar[stage.key] = n"
              @mouseleave="hoveredStar[stage.key] = 0"
              @click="ratings[stage.key] = n"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" stroke="none">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="field-group">
        <label for="category" class="field-label">Categoria</label>
        <select id="category" v-model="category" class="field-select" required>
          <option value="" disabled>Selecione uma categoria</option>
          <option value="bug">Bug</option>
          <option value="confusao_ux">Confusão de UX</option>
          <option value="sugestao">Sugestão</option>
        </select>
      </div>

      <div class="field-group">
        <label for="description" class="field-label">Descrição</label>
        <textarea
          id="description"
          v-model="description"
          class="field-textarea"
          rows="4"
          maxlength="1000"
          placeholder="Descreva sua experiência, problema ou sugestão em detalhes..."
        ></textarea>
        <span class="char-counter" :class="{ nearLimit: description.length > 900 }">
          {{ description.length }}/1000
        </span>
      </div>

      <button type="submit" class="submit-btn" :disabled="!isFormValid">
        Enviar Feedback
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  simulationId: { type: String, default: '' },
  reportId: { type: String, default: '' }
})

const emit = defineEmits(['submit'])

const stages = [
  { key: 'ingestao', label: 'Ingestão' },
  { key: 'ontologia', label: 'Ontologia' },
  { key: 'grafo', label: 'Grafo' },
  { key: 'ambiente', label: 'Ambiente' },
  { key: 'simulacao', label: 'Simulação' },
  { key: 'relatorio', label: 'Relatório' },
  { key: 'inspecao', label: 'Inspeção' }
]

const ratings = ref({
  ingestao: 0,
  ontologia: 0,
  grafo: 0,
  ambiente: 0,
  simulacao: 0,
  relatorio: 0,
  inspecao: 0
})

const hoveredStar = ref({
  ingestao: 0,
  ontologia: 0,
  grafo: 0,
  ambiente: 0,
  simulacao: 0,
  relatorio: 0,
  inspecao: 0
})

const category = ref('')
const description = ref('')
const isLoading = ref(false)
const isSuccess = ref(false)

const isVisible = computed(() => !!props.simulationId && !!props.reportId)

const isFormValid = computed(() => {
  const allRated = stages.every(s => ratings.value[s.key] > 0)
  return allRated && category.value !== '' && description.value.trim().length > 0
})

const handleSubmit = async () => {
  if (!isFormValid.value) return

  isLoading.value = true

  await new Promise(resolve => setTimeout(resolve, 600))

  const payload = {
    simulationId: props.simulationId,
    reportId: props.reportId,
    ratings: { ...ratings.value },
    category: category.value,
    description: description.value.trim(),
    timestamp: new Date().toISOString()
  }

  emit('submit', payload)
  isLoading.value = false
  isSuccess.value = true
}

// Reset form when props change
watch(() => [props.simulationId, props.reportId], () => {
  isSuccess.value = false
  isLoading.value = false
  category.value = ''
  description.value = ''
  stages.forEach(s => {
    ratings.value[s.key] = 0
    hoveredStar.value[s.key] = 0
  })
}, { immediate: true })
</script>

<style scoped>
.beta-feedback-wrapper {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
}

.beta-feedback-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.feedback-header {
  margin-bottom: var(--space-2);
}

.feedback-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-background);
  margin: 0 0 4px 0;
}

.feedback-subtitle {
  font-size: 12px;
  color: var(--color-muted);
  margin: 0;
}

.ratings-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-3);
}

.rating-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.rating-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stars {
  display: flex;
  gap: 4px;
}

.star-btn {
  background: none;
  border: none;
  padding: 2px;
  cursor: pointer;
  color: var(--color-outline);
  transition: color 0.15s ease, transform 0.15s ease;
  line-height: 0;
}

.star-btn:hover {
  transform: scale(1.15);
}

.star-btn.filled,
.star-btn.hovered {
  color: var(--color-primary);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-select,
.field-textarea {
  padding: 10px 12px;
  font-size: 14px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  color: var(--color-on-background);
  font-family: var(--font-human);
  transition: border-color 0.2s ease;
}

.field-select:focus,
.field-textarea:focus {
  outline: none;
  border-color: var(--color-on-background);
}

.field-select option {
  background: var(--color-surface);
  color: var(--color-on-background);
}

.field-textarea {
  resize: vertical;
  line-height: 1.5;
}

.char-counter {
  font-size: 11px;
  color: var(--color-disabled);
  text-align: right;
  font-family: var(--font-mono);
}

.char-counter.nearLimit {
  color: var(--color-warning);
}

.submit-btn {
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-surface);
  background: var(--color-on-background);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
  font-family: var(--font-human);
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.submit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Loading State */
.feedback-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-4);
  color: var(--color-muted);
  font-size: 14px;
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

/* Success State */
.feedback-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  text-align: center;
  color: var(--color-success);
}

.feedback-success svg {
  color: var(--color-success);
  margin-bottom: var(--space-1);
}

.feedback-success h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-background);
  margin: 0;
}

.feedback-success p {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
  max-width: 360px;
}

@media (max-width: 640px) {
  .ratings-section {
    grid-template-columns: 1fr;
  }
}
</style>

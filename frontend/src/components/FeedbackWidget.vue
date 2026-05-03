<template>
  <!-- Floating Action Button -->
  <button
    class="feedback-fab"
    :aria-label="t('feedback.widgetTitle')"
    @click="isOpen = true"
  >
    <Icon name="message-square" :size="20" />
  </button>

  <!-- Feedback Modal -->
  <BaseModal
    :open="isOpen"
    :title="t('feedback.widgetTitle')"
    size="md"
    @update:open="isOpen = $event; if (!$event) resetForm()"
  >
    <div v-if="submitted" class="feedback-success">
      <div class="success-icon">
        <Icon name="check" :size="32" />
      </div>
      <p class="success-message">{{ t('feedback.thankYou') }}</p>
      <BaseButton variant="primary" @click="closeModal">
        {{ t('common.close') }}
      </BaseButton>
    </div>

    <form v-else class="feedback-form" @submit.prevent="handleSubmit">
      <!-- Rating -->
      <div class="form-group">
        <label class="form-label">{{ t('feedback.ratingLabel') }} *</label>
        <div class="star-rating" role="radiogroup" :aria-label="t('feedback.ratingLabel')">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            class="star-btn"
            :class="{ active: n <= rating, hover: n <= hoverRating }"
            :aria-checked="n === rating"
            role="radio"
            @mouseenter="hoverRating = n"
            @mouseleave="hoverRating = 0"
            @click="rating = n"
          >
            <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" stroke="none">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </button>
        </div>
        <span v-if="rating > 0" class="rating-text">{{ ratingLabels[rating - 1] }}</span>
      </div>

      <!-- Category -->
      <div class="form-group">
        <label class="form-label">{{ t('feedback.categoryLabel') }} *</label>
        <select v-model="category" class="form-select" required>
          <option value="" disabled>{{ t('feedback.selectCategory') }}</option>
          <option value="bug">{{ t('feedback.categories.bug') }}</option>
          <option value="ux_confusion">{{ t('feedback.categories.uxConfusion') }}</option>
          <option value="suggestion">{{ t('feedback.categories.suggestion') }}</option>
        </select>
      </div>

      <!-- Comment -->
      <div class="form-group">
        <label class="form-label">
          {{ t('feedback.commentLabel') }}
          <span v-if="rating > 0 && rating <= 3" class="required-badge">*</span>
        </label>
        <textarea
          v-model="comment"
          class="form-textarea"
          :class="{ invalid: showCommentError }"
          rows="4"
          :placeholder="t('feedback.commentPlaceholder')"
        ></textarea>
        <div class="textarea-meta">
          <span v-if="showCommentError" class="error-hint">
            {{ t('feedback.commentMinChars') }}
          </span>
          <span class="char-count" :class="{ warn: comment.length < 10 && rating <= 3 && rating > 0 }">
            {{ comment.length }} chars
          </span>
        </div>
      </div>

      <!-- Attached IDs -->
      <div v-if="simulationId || reportId" class="form-group">
        <label class="form-label">{{ t('feedback.attachedLabel') }}</label>
        <div class="attached-chips">
          <span v-if="simulationId" class="chip">
            <Icon name="link" :size="12" />
            {{ simulationId }}
          </span>
          <span v-if="reportId" class="chip">
            <Icon name="file-text" :size="12" />
            {{ reportId }}
          </span>
        </div>
      </div>

      <!-- Error -->
      <div v-if="submitError" class="submit-error" role="alert">
        <Icon name="alert-circle" :size="16" />
        {{ submitError }}
      </div>

      <!-- Actions -->
      <div class="form-actions">
        <BaseButton
          variant="primary"
          type="submit"
          :loading="isSubmitting"
          :disabled="!isFormValid"
          brutalist
        >
          {{ t('feedback.submitBtn') }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from './base/BaseModal.vue'
import BaseButton from './base/BaseButton.vue'
import Icon from './Icon.vue'
import { createFeedback } from '../api/feedback'

const props = defineProps({
  stage: {
    type: String,
    required: true,
    validator: (v) => ['graph_build', 'env_setup', 'simulation', 'report', 'inspection'].includes(v),
  },
  simulationId: { type: String, default: null },
  reportId: { type: String, default: null },
})

const { t } = useI18n()

const isOpen = ref(false)
const rating = ref(0)
const hoverRating = ref(0)
const category = ref('')
const comment = ref('')
const isSubmitting = ref(false)
const submitted = ref(false)
const submitError = ref('')

const ratingLabels = [
  t('feedback.ratings.terrible'),
  t('feedback.ratings.bad'),
  t('feedback.ratings.ok'),
  t('feedback.ratings.good'),
  t('feedback.ratings.excellent'),
]

const showCommentError = computed(() => {
  if (rating.value <= 0) return false
  if (rating.value > 3) return false
  return comment.value.trim().length > 0 && comment.value.trim().length < 10
})

const isFormValid = computed(() => {
  if (rating.value < 1 || rating.value > 5) return false
  if (!category.value) return false
  if (rating.value <= 3 && comment.value.trim().length < 10) return false
  return true
})

const resetForm = () => {
  rating.value = 0
  hoverRating.value = 0
  category.value = ''
  comment.value = ''
  isSubmitting.value = false
  submitted.value = false
  submitError.value = ''
}

const closeModal = () => {
  isOpen.value = false
  resetForm()
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  isSubmitting.value = true
  submitError.value = ''

  try {
    await createFeedback({
      stage: props.stage,
      category: category.value,
      rating: rating.value,
      comment: comment.value.trim(),
      simulation_id: props.simulationId,
      report_id: props.reportId,
    })
    submitted.value = true
  } catch (err) {
    submitError.value = err?.message || t('feedback.submitError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* Floating Action Button */
.feedback-fab {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  width: 48px;
  height: 48px;
  border-radius: 0;
  border: 2px solid var(--color-on-background);
  background: var(--color-surface-elevated);
  color: var(--color-on-background);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 50;
  box-shadow: var(--shadow-brutalist);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.feedback-fab:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px var(--color-on-background);
}

.feedback-fab:active {
  transform: translate(0, 0);
  box-shadow: var(--shadow-brutalist);
}

/* Success state */
.feedback-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8) var(--space-4);
  text-align: center;
}

.success-icon {
  color: var(--color-success);
}

.success-message {
  font-family: var(--font-machine);
  font-size: var(--text-lg);
  color: var(--color-on-background);
}

/* Form */
.feedback-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.required-badge {
  color: var(--color-error);
}

/* Star rating */
.star-rating {
  display: flex;
  gap: var(--space-2);
}

.star-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: var(--space-1);
  color: var(--color-outline);
  transition: color 0.15s ease, transform 0.1s ease;
}

.star-btn:hover,
.star-btn.hover,
.star-btn.active {
  color: var(--color-warning);
}

.star-btn:active {
  transform: scale(0.9);
}

.rating-text {
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  color: var(--color-muted);
  margin-top: var(--space-1);
}

/* Select & Textarea */
.form-select,
.form-textarea {
  font-family: var(--font-body);
  font-size: var(--text-base);
  padding: var(--space-3);
  border: 1px solid var(--color-outline);
  border-radius: 0;
  background: var(--color-surface-elevated);
  color: var(--color-on-background);
  outline: none;
  transition: border-color 0.15s ease;
}

.form-select:focus,
.form-textarea:focus {
  border-color: var(--color-primary);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-textarea.invalid {
  border-color: var(--color-error);
}

.textarea-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-hint {
  font-size: var(--text-xs);
  color: var(--color-error);
}

.char-count {
  font-size: var(--text-xs);
  color: var(--color-muted);
}

.char-count.warn {
  color: var(--color-warning);
}

/* Attached chips */
.attached-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-muted);
}

/* Submit error */
.submit-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-error-container);
  color: var(--color-on-error-container);
  font-size: var(--text-sm);
  border: 1px solid var(--color-error);
}

/* Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-2);
}

@media (max-width: 480px) {
  .feedback-fab {
    bottom: var(--space-4);
    right: var(--space-4);
    width: 44px;
    height: 44px;
  }
}
</style>

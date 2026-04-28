<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-overlay" @click.self="close">
        <div :class="modalClasses">
          <div v-if="title" class="modal-header">
            <h3 class="modal-title">{{ title }}</h3>
            <button class="modal-close" @click="close" aria-label="Fechar">
              <Icon name="x" :size="20" />
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import Icon from '../Icon.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
})

const emit = defineEmits(['update:open'])

const modalClasses = computed(() => {
  return ['modal-content', `size-${props.size}`]
})

const close = () => emit('update:open', false)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}

.modal-content {
  background: var(--color-surface-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.size-sm { max-width: 400px; }
.size-md { max-width: 600px; }
.size-lg { max-width: 800px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-outline);
}

.modal-title {
  font-family: var(--font-machine);
  font-size: var(--text-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-on-background);
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: var(--space-1);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}

.modal-close:hover {
  color: var(--color-on-background);
  background: var(--color-surface-container-low);
}

.modal-body {
  padding: var(--space-5);
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-outline);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-content {
  transform: scale(0.96);
  opacity: 0;
}
.modal-enter-to .modal-content {
  transform: scale(1);
  opacity: 1;
}
.modal-leave-to .modal-content {
  transform: scale(0.98);
  opacity: 0;
}
</style>

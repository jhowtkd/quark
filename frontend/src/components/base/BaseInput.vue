<template>
  <div class="base-input-wrapper">
    <input
      v-if="type !== 'textarea'"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <textarea
      v-else
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      :rows="rows"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  type: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'password', 'email', 'number', 'textarea'].includes(v),
  },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  rows: { type: Number, default: 4 },
})

defineEmits(['update:modelValue'])

const inputClasses = computed(() => {
  const classes = ['base-input']
  if (props.error) classes.push('error')
  if (props.disabled) classes.push('disabled')
  return classes
})
</script>

<style scoped>
.base-input-wrapper {
  width: 100%;
}

.base-input {
  width: 100%;
  font-family: var(--font-human);
  font-size: var(--text-base);
  color: var(--color-on-background);
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--color-outline);
  border-radius: var(--radius-none);
  padding: var(--space-2) 0;
  transition: border-color 0.2s ease;
  outline: none;
}

.base-input::placeholder {
  color: var(--color-disabled);
}

.base-input:focus {
  border-bottom-color: var(--color-primary);
}

.base-input.error {
  border-bottom-color: var(--color-error);
}

.base-input.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

textarea.base-input {
  border: 2px solid var(--color-outline);
  padding: var(--space-3);
  resize: vertical;
}

textarea.base-input:focus {
  border-color: var(--color-primary);
}
</style>

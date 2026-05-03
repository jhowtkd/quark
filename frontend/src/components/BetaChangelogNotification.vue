<template>
  <div v-if="visible" class="changelog-banner" role="status">
    <div class="banner-content">
      <Icon name="file-text" :size="16" />
      <span class="banner-text">
        Novo changelog de beta disponível (semana de {{ changelogDate }}).
      </span>
      <a :href="changelogUrl" target="_blank" class="banner-link" @click="markSeen">
        Ver alterações
      </a>
    </div>
    <button class="banner-dismiss" aria-label="Dispensar" @click="dismiss">
      <Icon name="x" :size="14" />
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  changelogUrl: { type: String, required: true },
  changelogDate: { type: String, required: true },
})

const visible = ref(false)
const storageKey = computed(() => `beta_changelog_dismissed_${props.changelogDate}`)
const seenKey = computed(() => `beta_changelog_last_seen`)

const checkVisible = () => {
  const dismissed = localStorage.getItem(storageKey.value)
  if (dismissed === 'true') {
    visible.value = false
    return
  }
  const lastSeen = localStorage.getItem(seenKey.value)
  if (lastSeen && lastSeen >= props.changelogDate) {
    visible.value = false
    return
  }
  visible.value = true
}

const dismiss = () => {
  localStorage.setItem(storageKey.value, 'true')
  visible.value = false
}

const markSeen = () => {
  localStorage.setItem(seenKey.value, props.changelogDate)
}

onMounted(() => {
  checkVisible()
})
</script>

<style scoped>
.changelog-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-container-low);
  border-bottom: 2px solid var(--color-on-background);
  gap: var(--space-4);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
}

.banner-text {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  color: var(--color-on-background);
}

.banner-link {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  color: var(--color-primary);
  text-decoration: underline;
  white-space: nowrap;
}

.banner-link:hover {
  color: var(--color-primary-hover);
}

.banner-dismiss {
  background: transparent;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: var(--space-1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-dismiss:hover {
  color: var(--color-on-background);
}

@media (max-width: 480px) {
  .changelog-banner {
    flex-direction: column;
    align-items: flex-start;
  }
  .banner-dismiss {
    align-self: flex-end;
  }
}
</style>

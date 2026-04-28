<template>
  <nav class="report-outline" :class="{ collapsed: isCollapsed }">
    <button class="outline-toggle" @click="isCollapsed = !isCollapsed">
      <Icon :name="isCollapsed ? 'chevron-right' : 'chevron-left'" :size="16" />
    </button>
    <div v-show="!isCollapsed" class="outline-content">
      <h4 class="outline-title">Conteúdo</h4>
      <ul class="outline-list">
        <li
          v-for="heading in headings"
          :key="heading.id"
          :class="['outline-item', `level-${heading.level}`, { active: activeId === heading.id }]"
        >
          <a :href="`#${heading.id}`" @click.prevent="scrollTo(heading.id)">
            {{ heading.text }}
          </a>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  headings: { type: Array, required: true }, // [{ id, text, level }]
})

const isCollapsed = ref(false)
const activeId = ref('')

let observer = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          activeId.value = entry.target.id
        }
      })
    },
    { rootMargin: '-20% 0px -60% 0px', threshold: 0 }
  )

  props.headings.forEach((h) => {
    const el = document.getElementById(h.id)
    if (el) observer.observe(el)
  })
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})

const scrollTo = (id) => {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeId.value = id
  }
}
</script>

<style scoped>
.report-outline {
  position: sticky;
  top: 80px;
  width: 220px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  padding: var(--space-4);
  align-self: flex-start;
  transition: width 0.2s ease;
}

.report-outline.collapsed {
  width: 40px;
  padding: var(--space-2);
}

.outline-toggle {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  background: transparent;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: var(--space-1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.outline-toggle:hover {
  color: var(--color-on-background);
}

.outline-title {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--space-3);
  color: var(--color-on-background);
}

.outline-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.outline-item a {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-muted);
  text-decoration: none;
  padding: 2px 0;
  border-left: 2px solid transparent;
  padding-left: var(--space-2);
  transition: all 0.15s ease;
}

.outline-item.level-2 a {
  padding-left: var(--space-3);
}

.outline-item.level-3 a {
  padding-left: var(--space-4);
}

.outline-item a:hover {
  color: var(--color-on-background);
}

.outline-item.active a {
  color: var(--color-on-background);
  font-weight: var(--font-weight-medium);
  border-left-color: var(--color-primary);
}

@media (max-width: 1024px) {
  .report-outline {
    display: none;
  }
}
</style>

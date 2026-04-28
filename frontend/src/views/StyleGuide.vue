<template>
  <div class="style-guide">
    <header class="sg-header">
      <h1>Blueprint Noir v2 — Style Guide</h1>
      <ThemeToggle />
    </header>

    <nav class="sg-nav">
      <a v-for="section in sections" :key="section.id" :href="`#${section.id}`" class="sg-nav-link">
        {{ section.label }}
      </a>
    </nav>

    <main class="sg-main">
      <!-- Colors -->
      <section id="colors" class="sg-section">
        <h2>Colors</h2>
        <div class="sg-grid">
          <div v-for="token in colorTokens" :key="token.name" class="sg-swatch">
            <div class="sg-swatch-color" :style="{ background: `var(${token.name})` }" />
            <code class="sg-swatch-name">{{ token.name }}</code>
            <span class="sg-swatch-desc">{{ token.desc }}</span>
          </div>
        </div>
      </section>

      <!-- Typography -->
      <section id="typography" class="sg-section">
        <h2>Typography</h2>
        <div class="sg-stack">
          <p class="sg-text-4xl">Heading 4xl — Space Grotesk</p>
          <p class="sg-text-3xl">Heading 3xl — Space Grotesk</p>
          <p class="sg-text-2xl">Heading 2xl — Space Grotesk</p>
          <p class="sg-text-xl">Heading xl — Space Grotesk</p>
          <p class="sg-text-lg">Heading lg — Work Sans</p>
          <p class="sg-text-base">Body base — Work Sans</p>
          <p class="sg-text-sm">Body sm — Work Sans</p>
          <p class="sg-text-xs">Body xs — Work Sans</p>
        </div>
      </section>

      <!-- Shadows -->
      <section id="shadows" class="sg-section">
        <h2>Shadows</h2>
        <div class="sg-stack">
          <div class="sg-shadow-demo" style="box-shadow: var(--shadow-none)">shadow-none</div>
          <div class="sg-shadow-demo" style="box-shadow: var(--shadow-brutalist)">shadow-brutalist</div>
          <div class="sg-shadow-demo" style="box-shadow: var(--shadow-soft)">shadow-soft</div>
          <div class="sg-shadow-demo" style="box-shadow: var(--shadow-md)">shadow-md</div>
          <div class="sg-shadow-demo" style="box-shadow: var(--shadow-lg)">shadow-lg</div>
        </div>
      </section>

      <!-- Components -->
      <section id="components" class="sg-section">
        <h2>Components</h2>

        <h3>BaseButton</h3>
        <div class="sg-row">
          <BaseButton v-for="v in buttonVariants" :key="v" :variant="v">{{ v }}</BaseButton>
        </div>
        <div class="sg-row">
          <BaseButton brutalist>brutalist</BaseButton>
          <BaseButton loading>loading</BaseButton>
          <BaseButton disabled>disabled</BaseButton>
        </div>
        <div class="sg-row">
          <BaseButton size="sm">small</BaseButton>
          <BaseButton size="md">medium</BaseButton>
          <BaseButton size="lg">large</BaseButton>
        </div>

        <h3>BaseInput</h3>
        <div class="sg-stack" style="max-width: 400px">
          <BaseInput placeholder="Default input" />
          <BaseInput placeholder="Error input" error />
          <BaseInput placeholder="Disabled input" disabled />
          <BaseInput type="textarea" placeholder="Textarea" />
        </div>

        <h3>BaseCard</h3>
        <div class="sg-row">
          <BaseCard variant="default" padding="md">Default card</BaseCard>
          <BaseCard variant="elevated" padding="md">Elevated card</BaseCard>
          <BaseCard variant="outlined" padding="md">Outlined card</BaseCard>
          <BaseCard brutalist padding="md">Brutalist card</BaseCard>
        </div>

        <h3>BaseBadge</h3>
        <div class="sg-row">
          <BaseBadge v-for="v in badgeVariants" :key="v" :variant="v">{{ v }}</BaseBadge>
        </div>

        <h3>BaseModal</h3>
        <BaseButton @click="modalOpen = true">Open Modal</BaseButton>
        <BaseModal v-model:open="modalOpen" title="Example Modal">
          <p>This is the modal body content.</p>
          <template #footer>
            <BaseButton variant="ghost" @click="modalOpen = false">Cancel</BaseButton>
            <BaseButton @click="modalOpen = false">Confirm</BaseButton>
          </template>
        </BaseModal>
      </section>

      <!-- Skeletons -->
      <section id="skeletons" class="sg-section">
        <h2>Skeleton Loading</h2>
        <div class="sg-stack" style="max-width: 500px">
          <SkeletonText :lines="4" />
          <SkeletonTable :rows="3" :columns="3" />
          <SkeletonGraph :node-count="6" />
        </div>
      </section>

      <!-- Progress Steps -->
      <section id="progress" class="sg-section">
        <h2>Progress Steps</h2>
        <ProgressSteps :steps="sampleSteps" />
        <h3 style="margin-top: var(--space-6)">Vertical</h3>
        <ProgressSteps :steps="sampleSteps" orientation="vertical" />
      </section>

      <!-- Icons -->
      <section id="icons" class="sg-section">
        <h2>Icons</h2>
        <div class="sg-grid-icons">
          <div v-for="name in iconNames" :key="name" class="sg-icon-item">
            <Icon :name="name" :size="24" />
            <code>{{ name }}</code>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import Icon from '../components/Icon.vue'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import BaseCard from '../components/base/BaseCard.vue'
import BaseBadge from '../components/base/BaseBadge.vue'
import BaseModal from '../components/base/BaseModal.vue'
import SkeletonBlock from '../components/skeleton/SkeletonBlock.vue'
import SkeletonText from '../components/skeleton/SkeletonText.vue'
import SkeletonTable from '../components/skeleton/SkeletonTable.vue'
import SkeletonGraph from '../components/skeleton/SkeletonGraph.vue'
import ProgressSteps from '../components/ProgressSteps.vue'

const modalOpen = ref(false)

const sampleSteps = [
  { label: 'Upload', status: 'completed' },
  { label: 'Ontology', status: 'completed' },
  { label: 'Graph', status: 'active', detail: 'Building nodes...' },
  { label: 'Ready', status: 'pending' },
]

const sections = [
  { id: 'colors', label: 'Colors' },
  { id: 'typography', label: 'Typography' },
  { id: 'shadows', label: 'Shadows' },
  { id: 'components', label: 'Components' },
  { id: 'skeletons', label: 'Skeletons' },
  { id: 'progress', label: 'Progress' },
  { id: 'icons', label: 'Icons' },
]

const colorTokens = [
  { name: '--color-background', desc: 'Page background' },
  { name: '--color-surface', desc: 'Card/panel background' },
  { name: '--color-surface-elevated', desc: 'Modal/dropdown' },
  { name: '--color-surface-overlay', desc: 'Tooltip/toast' },
  { name: '--color-surface-container-low', desc: 'Subtle containers' },
  { name: '--color-surface-container-highest', desc: 'Strong containers' },
  { name: '--color-primary', desc: 'Brand/action' },
  { name: '--color-on-background', desc: 'Text on background' },
  { name: '--color-on-surface', desc: 'Text on surface' },
  { name: '--color-muted', desc: 'Secondary text' },
  { name: '--color-disabled', desc: 'Disabled text' },
  { name: '--color-outline', desc: 'Borders/dividers' },
  { name: '--color-error', desc: 'Destructive' },
  { name: '--color-success', desc: 'Positive' },
  { name: '--color-warning', desc: 'Caution' },
  { name: '--color-info', desc: 'Information' },
  { name: '--color-link', desc: 'Hyperlink' },
]

const buttonVariants = ['primary', 'secondary', 'outline', 'ghost', 'danger']
const badgeVariants = ['default', 'success', 'warning', 'error', 'info', 'accent']

const iconNames = [
  'sun', 'moon', 'monitor', 'log-out', 'external-link', 'refresh-cw',
  'maximize-2', 'minimize-2', 'chevron-down', 'chevron-up', 'diamond',
  'play', 'check', 'x', 'loader-2', 'file-text', 'bar-chart-3',
  'message-square', 'globe', 'alert-circle', 'info', 'circle',
]
</script>

<style scoped>
.style-guide {
  min-height: 100vh;
  background: var(--color-background);
  color: var(--color-on-background);
  font-family: var(--font-human);
}

.sg-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
}

.sg-header h1 {
  font-family: var(--font-machine);
  font-size: var(--text-2xl);
  margin: 0;
}

.sg-nav {
  position: sticky;
  top: 60px;
  display: flex;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  background: var(--color-surface-container-low);
  border-bottom: 1px solid var(--color-outline);
  overflow-x: auto;
}

.sg-nav-link {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  color: var(--color-muted);
  text-decoration: none;
  white-space: nowrap;
}

.sg-nav-link:hover {
  color: var(--color-on-background);
}

.sg-main {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.sg-section {
  margin-bottom: var(--space-12);
}

.sg-section h2 {
  font-family: var(--font-machine);
  font-size: var(--text-xl);
  margin-bottom: var(--space-4);
  border-bottom: 2px solid var(--color-outline);
  padding-bottom: var(--space-2);
}

.sg-section h3 {
  font-family: var(--font-machine);
  font-size: var(--text-lg);
  margin: var(--space-6) 0 var(--space-3);
}

.sg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-4);
}

.sg-swatch {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sg-swatch-color {
  height: 60px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
}

.sg-swatch-name {
  font-size: var(--text-xs);
  color: var(--color-muted);
}

.sg-swatch-desc {
  font-size: var(--text-xs);
  color: var(--color-disabled);
}

.sg-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.sg-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
}

.sg-shadow-demo {
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  font-family: var(--font-machine);
  font-size: var(--text-sm);
}

.sg-text-4xl { font-size: var(--text-4xl); font-family: var(--font-machine); }
.sg-text-3xl { font-size: var(--text-3xl); font-family: var(--font-machine); }
.sg-text-2xl { font-size: var(--text-2xl); font-family: var(--font-machine); }
.sg-text-xl { font-size: var(--text-xl); font-family: var(--font-machine); }
.sg-text-lg { font-size: var(--text-lg); }
.sg-text-base { font-size: var(--text-base); }
.sg-text-sm { font-size: var(--text-sm); }
.sg-text-xs { font-size: var(--text-xs); }

.sg-grid-icons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: var(--space-4);
}

.sg-icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
}

.sg-icon-item code {
  font-size: var(--text-xs);
  color: var(--color-muted);
}
</style>

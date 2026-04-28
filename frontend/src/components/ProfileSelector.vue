<template>
  <div class="profile-selector">
    <div class="selector-header">
      <span class="selector-label">PROFILE</span>
      <span class="selector-hint">Selecione o domínio de análise</span>
    </div>
    <div class="profile-grid">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="profile-card"
        :class="{ active: selectedProfile === profile.id }"
        :style="getCardStyle(profile)"
        @click="selectProfile(profile.id)"
      >
        <div class="profile-icon">{{ profile.icon }}</div>
        <div class="profile-name">{{ profile.name }}</div>
        <div class="profile-desc">{{ profile.description }}</div>
        <div v-if="selectedProfile === profile.id" class="profile-check"><Icon name="check" :size="16" /></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Icon from './Icon.vue'

const emit = defineEmits(['profile-selected'])

const profiles = [
  {
    id: 'generico',
    name: 'Genérico',
    description: 'Comportamento padrão atual',
    color: '#000000',
    accent: '#444444',
    light: '#f0f0f0',
    icon: '◈'
  },
  {
    id: 'marketing',
    name: 'Marketing',
    description: 'Percepção de marca, sentimento, campanhas',
    color: '#0066FF',
    accent: '#00CCFF',
    light: '#e6f2ff',
    icon: '◎'
  },
  {
    id: 'direito',
    name: 'Direito',
    description: 'Legislação, precedentes, compliance',
    color: '#8B4513',
    accent: '#D2691E',
    light: '#fdf5e6',
    icon: '⚖'
  },
  {
    id: 'economia',
    name: 'Economia',
    description: 'Indicadores macro, cenários financeiros',
    color: '#006400',
    accent: '#228B22',
    light: '#e6f5e6',
    icon: '⊕'
  },
  {
    id: 'saude',
    name: 'Saúde',
    description: 'Diretrizes clínicas, evidências',
    color: '#C41E3A',
    accent: '#FF6B6B',
    light: '#fff0f2',
    icon: '✚'
  }
]

const selectedProfile = ref('generico')

const getCardStyle = (profile) => {
  const isActive = selectedProfile.value === profile.id
  return {
    '--profile-color': profile.color,
    '--profile-accent': profile.accent,
    '--profile-light': profile.light,
    borderColor: isActive ? profile.color : '#e0e0e0',
    backgroundColor: isActive ? profile.light : '#fafafa',
    boxShadow: isActive ? `4px 4px 0 ${profile.color}` : 'none',
    transform: isActive ? 'translate(-2px, -2px)' : 'translate(0, 0)'
  }
}

const selectProfile = (profileId) => {
  selectedProfile.value = profileId
  localStorage.setItem('futuria_profile', profileId)
  // Apply profile to body for CSS variable scoping
  document.body.setAttribute('data-profile', profileId)
  emit('profile-selected', profileId)
}

onMounted(() => {
  const saved = localStorage.getItem('futuria_profile')
  if (saved && profiles.some(p => p.id === saved)) {
    selectedProfile.value = saved
    document.body.setAttribute('data-profile', saved)
  } else {
    document.body.setAttribute('data-profile', 'generico')
  }
})
</script>

<style scoped>
.profile-selector {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface-container-low);
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
}

.selector-label {
  font-weight: 700;
  color: var(--color-disabled);
  letter-spacing: 1px;
}

.selector-hint {
  color: var(--color-disabled);
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
  border: 2px solid var(--color-outline);
  background: var(--color-surface-container-low);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  text-align: center;
  min-height: 100px;
}

.profile-card:hover {
  border-color: var(--profile-color, var(--color-on-background)000);
  background: var(--profile-light, var(--color-surface-container-low));
}

.profile-card.active {
  border-width: 2px;
}

.profile-icon {
  font-size: 1.5rem;
  margin-bottom: 6px;
  color: var(--profile-color, var(--color-on-background));
}

.profile-name {
  font-family: 'Space Grotesk', monospace;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-on-background);
  margin-bottom: 4px;
}

.profile-desc {
  font-size: 0.65rem;
  color: var(--color-muted);
  line-height: 1.3;
  font-family: 'Work Sans', sans-serif;
}

.profile-check {
  position: absolute;
  top: 4px;
  right: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--profile-color, var(--color-on-background));
}

/* Responsive */
@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .profile-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .profile-desc {
    display: none;
  }
  
  .profile-card {
    min-height: 60px;
    padding: 10px 6px;
  }
}
</style>

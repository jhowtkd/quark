<template>
  <div v-if="enabled" ref="agentationRef"></div>
</template>

<script>
import { defineComponent, onMounted, onUnmounted, ref } from 'vue'

export default defineComponent({
  name: 'AgentationWrapper',
  setup() {
    const agentationRef = ref(null)
    const endpoint = import.meta.env.VITE_AGENTATION_ENDPOINT
    const enabled = Boolean(endpoint)
    let root = null

    onMounted(async () => {
      if (enabled && agentationRef.value) {
        // Lazy load React and agentation only when needed
        const [{ createRoot }, React, { Agentation }] = await Promise.all([
          import('react-dom/client'),
          import('react'),
          import('agentation')
        ])

        const container = document.createElement('div')
        agentationRef.value.appendChild(container)
        root = createRoot(container)
        root.render(React.createElement(Agentation, {
          endpoint,
          onSessionCreated: (sessionId) => {
            // DEBUG: Agentation session created
            void sessionId
          }
        }))
      }
    })

    onUnmounted(() => {
      if (root) {
        root.unmount()
      }
    })

    return { agentationRef, enabled }
  }
})
</script>

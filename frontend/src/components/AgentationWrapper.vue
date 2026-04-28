<template>
  <div v-if="enabled" ref="agentationRef"></div>
</template>

<script>
import { defineComponent, onMounted, onUnmounted, ref } from 'vue'
import { createRoot } from 'react-dom/client'
import React from 'react'
import { Agentation } from 'agentation'

export default defineComponent({
  name: 'AgentationWrapper',
  setup() {
    const agentationRef = ref(null)
    const endpoint = import.meta.env.VITE_AGENTATION_ENDPOINT
    const enabled = Boolean(endpoint)
    let root = null

    onMounted(() => {
      if (enabled && agentationRef.value) {
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

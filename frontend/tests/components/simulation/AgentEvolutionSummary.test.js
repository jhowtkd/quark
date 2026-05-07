import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentEvolutionSummary from '../../../src/components/simulation/AgentEvolutionSummary.vue'

const tFn = (key) => key

describe('AgentEvolutionSummary', () => {
  const mountComponent = (props = {}) => {
    return mount(AgentEvolutionSummary, {
      props,
      global: { mocks: { $t: tFn } },
    })
  }

  it('renders average fatigue, polarization, and narrative alignment', () => {
    const evolution = {
      summary: {
        averages: {
          fatigue: 0.22,
          polarization_risk: 0.31,
          narrative_alignment: 0.57,
        },
        top_changed_agents: [
          { agent_id: 1, agent_name: 'Alice', change_score: 0.42 },
        ],
      },
    }

    const wrapper = mountComponent({ evolution })

    expect(wrapper.text()).toContain('0.22')
    expect(wrapper.text()).toContain('0.31')
    expect(wrapper.text()).toContain('0.57')
  })

  it('renders largest changed agents', () => {
    const evolution = {
      summary: {
        averages: {
          fatigue: 0.22,
          polarization_risk: 0.31,
          narrative_alignment: 0.57,
        },
        top_changed_agents: [
          { agent_id: 1, agent_name: 'Alice', change_score: 0.42 },
          { agent_id: 2, agent_name: 'Bob', change_score: 0.35 },
        ],
      },
    }

    const wrapper = mountComponent({ evolution })

    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
  })

  it('shows empty state when agent_evolution is missing', () => {
    const wrapper = mountComponent({ evolution: null })

    expect(wrapper.find('[role="status"]').exists()).toBe(true)
  })
})

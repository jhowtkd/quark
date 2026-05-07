import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentEvolutionInspector from '../../../src/components/simulation/AgentEvolutionInspector.vue'

const tFn = (key) => {
  const translations = {
    'evolution.mostInfluenced': 'Mais Influenciados',
    'evolution.mostInfluential': 'Mais Influentes',
    'evolution.mostPolarized': 'Mais Polarizados',
    'evolution.metricTimeline': 'Timeline de Métricas',
    'evolution.influence': 'Influência',
    'evolution.polarization': 'Polarização',
    'evolution.noEvidence': 'sem evidencia suficiente',
  }
  return translations[key] || key
}

describe('AgentEvolutionInspector', () => {
  const mountComponent = (props = {}) => {
    return mount(AgentEvolutionInspector, {
      props,
      global: { mocks: { $t: tFn } },
    })
  }

  it('renders most influenced agents', () => {
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
      snapshots: {
        '1': {
          agent_id: 1,
          agent_name: 'Alice',
          round_num: 5,
          social_influence: 0.45,
          polarization_risk: 0.31,
          fatigue: 0.22,
          evidence_openness: 0.33,
          narrative_alignment: 0.57,
          trust_level: 0.60,
        },
      },
      events: [
        {
          agent_id: 1,
          round_num: 1,
          metric_name: 'social_influence',
          delta: 0.02,
          causes: ['CREATE_POST (success)'],
        },
      ],
    }

    const wrapper = mountComponent({ evolution })
    expect(wrapper.text()).toContain('Alice')
  })

  it('shows "sem evidencia suficiente" when snapshots are absent', () => {
    const wrapper = mountComponent({ evolution: {} })
    expect(wrapper.text()).toContain('sem evidencia suficiente')
  })
})

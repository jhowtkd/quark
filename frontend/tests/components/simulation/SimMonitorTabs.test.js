import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimMonitorTabs from '../../../src/components/simulation/SimMonitorTabs.vue'
import { mockRunningState, mockActions } from '../../mocks/simulationState.js'

describe('SimMonitorTabs', () => {
  it('renders three tabs', () => {
    const wrapper = mount(SimMonitorTabs, {
      props: { state: mockRunningState, actions: mockActions },
    })
    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs.length).toBe(3)
    expect(wrapper.text()).toContain('Visão Geral')
    expect(wrapper.text()).toContain('Agentes')
    expect(wrapper.text()).toContain('Linha do Tempo')
  })

  it('switches tabs on click', async () => {
    const wrapper = mount(SimMonitorTabs, {
      props: { state: mockRunningState, actions: mockActions },
    })
    const tabs = wrapper.findAll('[role="tab"]')
    await tabs[1].trigger('click')
    expect(wrapper.find('.agents-tab').exists()).toBe(true)
  })
})

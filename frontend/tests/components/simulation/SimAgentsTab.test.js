import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimAgentsTab from '../../../src/components/simulation/SimAgentsTab.vue'
import { mockActions } from '../../mocks/simulationState.js'

describe('SimAgentsTab', () => {
  it('lists unique agents from actions', () => {
    const wrapper = mount(SimAgentsTab, {
      props: { actions: mockActions },
    })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).toContain('Charlie')
  })

  it('filters by name', async () => {
    const wrapper = mount(SimAgentsTab, {
      props: { actions: mockActions },
    })
    const input = wrapper.find('input[type="text"]')
    await input.setValue('ali')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).not.toContain('Bob')
  })
})

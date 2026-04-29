import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimTimelineTab from '../../../src/components/simulation/SimTimelineTab.vue'
import SimActionFeedItem from '../../../src/components/simulation/SimActionFeedItem.vue'
import { mockActions } from '../../mocks/simulationState.js'

describe('SimTimelineTab', () => {
  it('renders all actions by default', () => {
    const wrapper = mount(SimTimelineTab, {
      props: { actions: mockActions },
    })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.findAllComponents(SimActionFeedItem).length).toBe(mockActions.length)
  })

  it('filters by platform', async () => {
    const wrapper = mount(SimTimelineTab, {
      props: { actions: mockActions },
    })
    // Find "Plaza" toggle and click to deselect
    const chips = wrapper.findAll('.toggle-chip')
    const plazaChip = chips.find(c => c.text() === 'Plaza')
    await plazaChip.trigger('click')
    // Now only reddit (Community) actions should show (4 reddit actions in mock)
    expect(wrapper.findAllComponents(SimActionFeedItem).length).toBe(4)
  })
})

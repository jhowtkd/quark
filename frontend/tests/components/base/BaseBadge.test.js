import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseBadge from '../../../src/components/base/BaseBadge.vue'

describe('BaseBadge', () => {
  it('renders text', () => {
    const wrapper = mount(BaseBadge, { slots: { default: 'Badge' } })
    expect(wrapper.text()).toBe('Badge')
  })

  it('renders success variant', () => {
    const wrapper = mount(BaseBadge, { props: { variant: 'success' }, slots: { default: 'OK' } })
    expect(wrapper.classes()).toContain('variant-success')
  })

  it('renders error variant', () => {
    const wrapper = mount(BaseBadge, { props: { variant: 'error' }, slots: { default: 'Error' } })
    expect(wrapper.classes()).toContain('variant-error')
  })

  it('renders warning variant', () => {
    const wrapper = mount(BaseBadge, { props: { variant: 'warning' }, slots: { default: 'Warn' } })
    expect(wrapper.classes()).toContain('variant-warning')
  })

  it('renders info variant', () => {
    const wrapper = mount(BaseBadge, { props: { variant: 'info' }, slots: { default: 'Info' } })
    expect(wrapper.classes()).toContain('variant-info')
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import BetaFeedbackForm from '../../src/components/BetaFeedbackForm.vue'

describe('BetaFeedbackForm', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  const mountComponent = (props = {}) => {
    return mount(BetaFeedbackForm, {
      props: { simulationId: 'sim-123', reportId: 'rep-456', ...props }
    })
  }

  it('renders all 7 star rating groups', () => {
    const wrapper = mountComponent()
    const labels = wrapper.findAll('.rating-label')
    expect(labels.length).toBe(7)
    expect(labels.at(0).text()).toBe('Ingestão')
    expect(labels.at(1).text()).toBe('Ontologia')
    expect(labels.at(2).text()).toBe('Grafo')
    expect(labels.at(3).text()).toBe('Ambiente')
    expect(labels.at(4).text()).toBe('Simulação')
    expect(labels.at(5).text()).toBe('Relatório')
    expect(labels.at(6).text()).toBe('Inspeção')
  })

  it('emits submit event with correct payload when form is filled and submitted', async () => {
    const wrapper = mountComponent()

    // Fill all 7 star ratings (click 3rd star for each)
    const starGroups = wrapper.findAll('.stars')
    expect(starGroups.length).toBe(7)
    for (const group of starGroups) {
      const stars = group.findAll('.star-btn')
      await stars.at(2).trigger('click')
    }

    // Select category
    const select = wrapper.find('.field-select')
    await select.setValue('sugestao')

    // Fill description
    const textarea = wrapper.find('.field-textarea')
    await textarea.setValue('Ótima experiência, mas precisa de mais filtros.')

    await nextTick()

    // Submit form
    await wrapper.find('.beta-feedback-form').trigger('submit')

    // Fast-forward past the artificial loading delay
    await vi.advanceTimersByTimeAsync(700)
    await flushPromises()
    await nextTick()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted.length).toBe(1)

    const payload = emitted[0][0]
    expect(payload.simulationId).toBe('sim-123')
    expect(payload.reportId).toBe('rep-456')
    expect(payload.category).toBe('sugestao')
    expect(payload.description).toBe('Ótima experiência, mas precisa de mais filtros.')
    expect(payload.ratings).toEqual({
      ingestao: 3,
      ontologia: 3,
      grafo: 3,
      ambiente: 3,
      simulacao: 3,
      relatorio: 3,
      inspecao: 3
    })
    expect(typeof payload.timestamp).toBe('string')
    expect(payload.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/)
  })

  it('shows success message after submit', async () => {
    const wrapper = mountComponent()

    // Fill all ratings
    const starGroups = wrapper.findAll('.stars')
    for (const group of starGroups) {
      const stars = group.findAll('.star-btn')
      await stars.at(1).trigger('click')
    }

    await wrapper.find('.field-select').setValue('bug')
    await wrapper.find('.field-textarea').setValue('Encontrei um erro na simulação.')
    await nextTick()

    await wrapper.find('.beta-feedback-form').trigger('submit')
    await vi.advanceTimersByTimeAsync(700)
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.feedback-success').exists()).toBe(true)
    expect(wrapper.text()).toContain('Obrigado pelo seu feedback')
  })

  it('does not render when props are missing', () => {
    const wrapperMissingSim = mount(BetaFeedbackForm, {
      props: { simulationId: '', reportId: 'rep-456' }
    })
    expect(wrapperMissingSim.find('.beta-feedback-wrapper').exists()).toBe(false)

    const wrapperMissingRep = mount(BetaFeedbackForm, {
      props: { simulationId: 'sim-123', reportId: '' }
    })
    expect(wrapperMissingRep.find('.beta-feedback-wrapper').exists()).toBe(false)

    const wrapperMissingBoth = mount(BetaFeedbackForm, {
      props: { simulationId: '', reportId: '' }
    })
    expect(wrapperMissingBoth.find('.beta-feedback-wrapper').exists()).toBe(false)
  })

  it('disables submit button when form is incomplete', async () => {
    const wrapper = mountComponent()
    const btn = wrapper.find('.submit-btn')
    expect(btn.attributes('disabled')).toBeDefined()

    // Fill only ratings
    const starGroups = wrapper.findAll('.stars')
    for (const group of starGroups) {
      const stars = group.findAll('.star-btn')
      await stars.at(0).trigger('click')
    }
    await nextTick()
    expect(btn.attributes('disabled')).toBeDefined()

    // Add category but no description
    await wrapper.find('.field-select').setValue('bug')
    await nextTick()
    expect(btn.attributes('disabled')).toBeDefined()

    // Add description
    await wrapper.find('.field-textarea').setValue('Descrição completa.')
    await nextTick()
    expect(btn.attributes('disabled')).toBeUndefined()
  })

  it('shows loading state during submit', async () => {
    const wrapper = mountComponent()

    const starGroups = wrapper.findAll('.stars')
    for (const group of starGroups) {
      const stars = group.findAll('.star-btn')
      await stars.at(0).trigger('click')
    }
    await wrapper.find('.field-select').setValue('confusao_ux')
    await wrapper.find('.field-textarea').setValue('Não entendi a interface.')
    await nextTick()

    wrapper.find('.beta-feedback-form').trigger('submit')
    await nextTick()

    expect(wrapper.find('.feedback-loading').exists()).toBe(true)
  })
})

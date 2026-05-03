import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import FeedbackWidget from '../../src/components/FeedbackWidget.vue'

const tFn = (key) => {
  const translations = {
    'feedback.widgetTitle': 'Feedback sobre esta etapa',
    'feedback.ratingLabel': 'Nota',
    'feedback.categoryLabel': 'Categoria',
    'feedback.selectCategory': 'Selecione uma categoria',
    'feedback.categories.bug': 'Bug',
    'feedback.categories.uxConfusion': 'Confusão de UX',
    'feedback.categories.suggestion': 'Sugestão',
    'feedback.commentLabel': 'Comentário',
    'feedback.commentPlaceholder': 'Descreva sua experiência...',
    'feedback.commentMinChars': 'Mínimo 10 caracteres',
    'feedback.attachedLabel': 'Anexado',
    'feedback.submitBtn': 'Enviar',
    'feedback.thankYou': 'Obrigado pelo seu feedback!',
    'feedback.submitError': 'Erro ao enviar feedback',
    'feedback.ratings.terrible': 'Péssimo',
    'feedback.ratings.bad': 'Ruim',
    'feedback.ratings.ok': 'OK',
    'feedback.ratings.good': 'Bom',
    'feedback.ratings.excellent': 'Excelente',
    'common.close': 'Fechar',
  }
  return translations[key] || key
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: tFn })
}))

const mockCreateFeedback = vi.fn(() => Promise.resolve({ success: true, data: { feedback_id: 'fb_abc123' } }))

vi.mock('../../src/api/feedback.js', () => ({
  createFeedback: (...args) => mockCreateFeedback(...args)
}))

describe('FeedbackWidget', () => {
  beforeEach(() => {
    mockCreateFeedback.mockClear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  const mountComponent = (props = {}) => {
    return mount(FeedbackWidget, {
      props: { stage: 'simulation', ...props }
    })
  }

  it('renders FAB button', () => {
    const wrapper = mountComponent()
    expect(wrapper.find('.feedback-fab').exists()).toBe(true)
  })

  it('opens modal when FAB is clicked', async () => {
    const wrapper = mountComponent()
    await wrapper.find('.feedback-fab').trigger('click')
    await nextTick()
    // Modal is teleported to body
    expect(document.body.querySelector('.modal-content')).toBeTruthy()
  })

  it('submits feedback with correct payload', async () => {
    const wrapper = mountComponent({ simulationId: 'sim-123', reportId: 'rep-456' })
    await wrapper.find('.feedback-fab').trigger('click')
    await nextTick()

    // Fill rating (click 4th star)
    const stars = document.body.querySelectorAll('.star-btn')
    await stars[3].dispatchEvent(new Event('click'))
    await nextTick()

    // Fill category
    const select = document.body.querySelector('.form-select')
    select.value = 'suggestion'
    await select.dispatchEvent(new Event('change'))
    await nextTick()

    // Fill comment
    const textarea = document.body.querySelector('.form-textarea')
    textarea.value = 'Great experience overall'
    await textarea.dispatchEvent(new Event('input'))
    await nextTick()

    // Submit
    const form = document.body.querySelector('.feedback-form')
    await form.dispatchEvent(new Event('submit'))
    await flushPromises()
    await nextTick()

    expect(mockCreateFeedback).toHaveBeenCalledTimes(1)
    const payload = mockCreateFeedback.mock.calls[0][0]
    expect(payload.stage).toBe('simulation')
    expect(payload.rating).toBe(4)
    expect(payload.category).toBe('suggestion')
    expect(payload.comment).toBe('Great experience overall')
    expect(payload.simulation_id).toBe('sim-123')
    expect(payload.report_id).toBe('rep-456')
  })

  it('requires comment when rating <= 3', async () => {
    const wrapper = mountComponent()
    await wrapper.find('.feedback-fab').trigger('click')
    await nextTick()

    // Click 2nd star (rating = 2)
    const stars = document.body.querySelectorAll('.star-btn')
    await stars[1].dispatchEvent(new Event('click'))
    await nextTick()

    // Fill category
    const select = document.body.querySelector('.form-select')
    select.value = 'bug'
    await select.dispatchEvent(new Event('change'))
    await nextTick()

    // Short comment
    const textarea = document.body.querySelector('.form-textarea')
    textarea.value = 'short'
    await textarea.dispatchEvent(new Event('input'))
    await nextTick()

    // Submit button should be disabled
    const btn = document.body.querySelector('.base-button')
    expect(btn.disabled).toBe(true)
  })

  it('shows success state after submit', async () => {
    const wrapper = mountComponent()
    await wrapper.find('.feedback-fab').trigger('click')
    await nextTick()

    // Fill rating 5
    const stars = document.body.querySelectorAll('.star-btn')
    await stars[4].dispatchEvent(new Event('click'))
    await nextTick()

    // Fill category
    const select = document.body.querySelector('.form-select')
    select.value = 'suggestion'
    await select.dispatchEvent(new Event('change'))
    await nextTick()

    // Submit
    const form = document.body.querySelector('.feedback-form')
    await form.dispatchEvent(new Event('submit'))
    await flushPromises()
    await nextTick()

    expect(document.body.querySelector('.feedback-success')).toBeTruthy()
  })
})

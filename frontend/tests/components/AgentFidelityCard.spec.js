import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import Step5Interaction from '../../src/components/Step5Interaction.vue'

const i18nMessages = {
  'step5.dashboard.overviewTab': 'Visão Geral',
  'step5.dashboard.chatTab': 'Chat',
  'step5.dashboard.surveyTab': 'Pesquisa',
  'step5.dashboard.agents': 'Agentes',
  'step5.dashboard.rounds': 'Rounds',
  'step5.dashboard.actions': 'Ações',
  'step5.dashboard.posts': 'Posts',
  'step5.dashboard.likes': 'Likes',
  'step5.dashboard.quotes': 'Quotes',
  'step5.dashboard.noSimulation': 'Selecione uma simulação para visualizar o dashboard.',
  'step5.dashboard.noTimelineData': 'Nenhum dado de timeline disponível.',
  'step5.dashboard.loadMore': 'Carregar mais',
  'step5.dashboard.byRound': 'Por Round',
  'step5.dashboard.byHour': 'Por Hora',
  'step5.dashboard.topAgents': 'Agentes mais ativos',
  'step5.dashboard.viewAll': 'Ver todos',
  'step5.interactiveTools': 'Ferramentas de Interação',
  'step5.agentsAvailable': '{count} ativos em jogo',
  'step5.chatWithReportAgent': 'Dialogar c/ Agente Repórter',
  'step5.chatWithAgent': 'Conversa Individual c/ Simulado',
  'step5.selectChatTarget': 'Especifique quem contatar',
  'step5.sendSurvey': 'Aplicar questionário',
  'step5.reportAgentChat': 'Agente Repórter - Salas',
  'step5.reportAgentDesc': 'Um repórter onisciente da história que sabe tudo que aconteceu.',
  'step5.toolInsightForge': 'InsightForge Atribuição',
  'step5.toolInsightForgeDesc': 'Alinha as percepções do contexto combinando as realidades.',
  'step5.toolPanoramaSearch': 'PanoramaSearch Histórico',
  'step5.toolPanoramaSearchDesc': 'Levantamento panorâmico que restabelece as conexões.',
  'step5.toolQuickSearch': 'QuickSearch Pesquisa Veloz',
  'step5.toolQuickSearchDesc': 'Consulta básica usando GraphRAG para encontrar o essencial.',
  'step5.toolInterviewSubAgent': 'InterviewSubAgent Questionador',
  'step5.toolInterviewSubAgentDesc': 'Realiza levantamentos contatando vários simulados paralelos e simultâneos.',
  'step5.profileBio': 'Sinopse',
  'step5.chatEmptyReportAgent': 'Mande uma mensagem para esclarecer as percepções do Relatório',
  'step5.chatEmptyAgent': 'Troque ideia para extrair a ótica pessoal deste NPC simulado',
  'step5.chatInputPlaceholder': 'Digite de forma clara...',
  'step5.selectSurveyTarget': 'Marque os simulados avaliados',
  'step5.selectedCount': 'Escolhidos {selected} de {total}',
  'step5.surveyQuestions': 'Questionário em Volume',
  'step5.surveyInputPlaceholder': 'Escreva a pergunta ou desafio a ser disparado...',
  'step5.submitSurvey': 'Remeter',
  'step5.surveyResults': 'Ver Resultados',
  'step5.surveyResultsCount': '{count} indivíduos responderam',
  'step5.selectAll': 'Marcar Grelha',
  'step5.clearSelection': 'Inverter',
  'step5.errorOccurred': 'Ocorreu uma fatalidade de sistema: {error}',
  'step5.noResponse': 'Sem retorno',
  'step5.requestFailed': 'O envio da requisição abortou',
  'step5.selectAgentFirst': 'Especifique o indivíduo simulado para começar',
  'step5.senderYou': 'Você',
  'step5.senderReportAgent': 'Agente Repórter',
  'step5.senderAgent': 'Agente',
  'step2.unknownProfession': 'Profissão desconhecida',
  'log.step5Init': 'Atalhos Visuais e Motores Operantes de Chat Carregados Para Interligações Neurais',
  'log.loadProfilesFailed': 'Nenhuma Vida Digital Acoplada Em Seu Cérebro Relacional SQL Devido Queda do Loader Otimizador Paralelo Interno de Dados Simétricos Ocultos do JSON de Output Estático do Pipeline: {error}',
  'log.loadedProfiles': 'Vidas Digitais Acopladas: {count} Personalidades Sociais Plenas',
  'log.loadReportData': 'Puxando Cache Dissecado Visual Mínimo da Leitura Dinâmica Otimizada com Chave Numérica Identificadora Absoluta da Geração Processada no Bloco Arquivos Python e Markdown Local Hospedados Ocultos no Diretório Back do Relatório de Visão Consolidado: {id}',
  'log.reportDataLoaded': 'Arquivos Encontrados E Dispostos Com Prazer...',
  'log.loadReportFailed': 'Queda ao Montar Arquivo Markdown e Visualizações em Caixa Lógica Dinâmica De HTML e CSS Intercalados por Framework Reativo Devido Ausência dos Blocos de Textos Separados por Fases de Discursos Relacionais ReACT: {error}',
  'log.loadReportLogFailed': 'Sem Registros Auxiliares Lidos: {error}',
  'contamination.contentRemoved': 'Conteúdo removido por violação de política',
}

const mockT = (key, params) => {
  let msg = i18nMessages[key] || key
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      msg = msg.replace(new RegExp(`{${k}}`, 'g'), v)
    })
  }
  return msg
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: mockT,
    $t: mockT
  })
}))

const mockGetSimulation = vi.fn(() => Promise.resolve({
  success: true,
  data: {
    total_rounds: 10,
    current_round: 5,
    io_validation: {
      passed: true,
      coverage_ratio: 1.0,
      missing_count: 0,
      spurious_count: 0,
      missing_agent_ids: [],
      spurious_agent_ids: [],
    }
  }
}))
const mockGetAgentStats = vi.fn(() => Promise.resolve({
  success: true,
  data: {
    stats: [
      { agent_id: 1, agent_name: 'Alice', total_actions: 50, twitter_actions: 30, reddit_actions: 20, action_types: { CREATE_POST: 20, LIKE: 15, COMMENT: 15 } },
    ]
  }
}))
const mockGetSimulationTimeline = vi.fn(() => Promise.resolve({
  success: true,
  data: { timeline: [] }
}))
const mockGetSimulationActions = vi.fn(() => Promise.resolve({ success: true, data: { count: 100, total: 100 } }))
const mockGetSimulationPosts = vi.fn(() => Promise.resolve({ success: true, data: { count: 25, total: 25 } }))

vi.mock('../../src/api/simulation', () => ({
  interviewAgents: vi.fn(() => Promise.resolve({ success: true, data: {} })),
  getSimulationProfilesRealtime: vi.fn(() => Promise.resolve({ success: true, data: { profiles: [] } })),
  getSimulation: (...args) => mockGetSimulation(...args),
  getAgentStats: (...args) => mockGetAgentStats(...args),
  getSimulationTimeline: (...args) => mockGetSimulationTimeline(...args),
  getSimulationActions: (...args) => mockGetSimulationActions(...args),
  getSimulationPosts: (...args) => mockGetSimulationPosts(...args),
}))

vi.mock('../../src/api/report', () => ({
  chatWithReport: vi.fn(() => Promise.resolve({ success: true, data: { response: 'hello' } })),
  getReport: vi.fn(() => Promise.resolve({ success: true, data: {} })),
  getAgentLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [] } })),
}))

vi.mock('../../src/utils/payloadValidator', () => ({
  detectContamination: vi.fn(() => ({ severity: 'clean', reasons: [] })),
  sanitizeContent: vi.fn((c) => c),
  validateChatHistory: vi.fn(() => true)
}))

global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) { this.callback = callback }
  observe() {}
  disconnect() {}
  unobserve() {}
}

describe('Step5Interaction - AgentFidelityCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetSimulation.mockReset()
    mockGetAgentStats.mockReset()
    mockGetSimulationActions.mockReset()
    mockGetSimulationPosts.mockReset()
    mockGetSimulationTimeline.mockReset()

    // Default implementations
    mockGetAgentStats.mockImplementation(() => Promise.resolve({
      success: true,
      data: { stats: [] }
    }))
    mockGetSimulationActions.mockImplementation(() => Promise.resolve({ success: true, data: { count: 0 } }))
    mockGetSimulationPosts.mockImplementation(() => Promise.resolve({ success: true, data: { count: 0 } }))
    mockGetSimulationTimeline.mockImplementation(() => Promise.resolve({ success: true, data: { timeline: [] } }))
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders fidelity card when io_validation is present and passed', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
        io_validation: {
          passed: true,
          coverage_ratio: 1.0,
          missing_count: 0,
          spurious_count: 0,
          missing_agent_ids: [],
          spurious_agent_ids: [],
        }
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.fidelity-card').exists()).toBe(true)
    expect(wrapper.find('.fidelity-card-title').text()).toContain('Fidelidade de Agentes')
    expect(wrapper.find('.fidelity-badge').text()).toContain('OK')
    expect(wrapper.find('.fidelity-badge').classes()).toContain('badge-green')
    expect(wrapper.find('.coverage-value').text()).toBe('100%')
  })

  it('shows yellow badge when passed is false', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
        io_validation: {
          passed: false,
          coverage_ratio: 0.85,
          missing_count: 1,
          spurious_count: 0,
          missing_agent_ids: [9],
          spurious_agent_ids: [],
        }
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.fidelity-badge').text()).toContain('Atenção')
    expect(wrapper.find('.fidelity-badge').classes()).toContain('badge-yellow')
    expect(wrapper.find('.coverage-value').text()).toBe('85%')
  })

  it('shows missing agents list when missing_count > 0', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
        io_validation: {
          passed: false,
          coverage_ratio: 0.9,
          missing_count: 1,
          spurious_count: 0,
          missing_agent_ids: [9],
          spurious_agent_ids: [],
        }
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    const toggle = wrapper.findAll('.fidelity-toggle').find(el => el.text().includes('ausentes'))
    expect(toggle).toBeTruthy()

    await toggle.trigger('click')
    await nextTick()

    const tags = wrapper.findAll('.fidelity-missing')
    expect(tags.length).toBe(1)
    expect(tags[0].text()).toContain('ID 9')
  })

  it('shows spurious agents list when spurious_count > 0', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
        io_validation: {
          passed: false,
          coverage_ratio: 1.0,
          missing_count: 0,
          spurious_count: 1,
          missing_agent_ids: [],
          spurious_agent_ids: [10],
        }
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    const toggle = wrapper.findAll('.fidelity-toggle').find(el => el.text().includes('espúrios'))
    expect(toggle).toBeTruthy()

    await toggle.trigger('click')
    await nextTick()

    const tags = wrapper.findAll('.fidelity-spurious')
    expect(tags.length).toBe(1)
    expect(tags[0].text()).toContain('ID 10')
  })

  it('shows tooltip when missing_count > 0', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
        io_validation: {
          passed: false,
          coverage_ratio: 0.85,
          missing_count: 1,
          spurious_count: 0,
          missing_agent_ids: [9],
          spurious_agent_ids: [],
        }
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    const tooltip = wrapper.find('.fidelity-tooltip')
    expect(tooltip.exists()).toBe(true)
    expect(tooltip.attributes('title')).toContain('Alguns agentes previstos nao produziram acoes')
  })

  it('does not render fidelity card when io_validation is absent', async () => {
    mockGetSimulation.mockImplementation(() => Promise.resolve({
      success: true,
      data: {
        total_rounds: 10,
        current_round: 5,
      }
    }))

    const wrapper = mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1' },
      global: { mocks: { $t: mockT } }
    })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.fidelity-card').exists()).toBe(false)
  })
})

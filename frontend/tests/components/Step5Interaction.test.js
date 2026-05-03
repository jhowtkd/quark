import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import Step5Interaction from '../../src/components/Step5Interaction.vue'
import { mockActions } from '../mocks/simulationState.js'

const tFn = (key, params = {}) => {
  const translations = {
    'step5.dashboard.overviewTab': 'Visão Geral',
    'step5.dashboard.chatTab': 'Chat',
    'step5.dashboard.surveyTab': 'Pesquisa',
    'step5.dashboard.exploreTab': 'Explorar',
    'step5.dashboard.compareTab': 'Comparar',
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
    'step5.explorer.title': 'Explorar Ações',
    'step5.explorer.searchPlaceholder': 'Buscar em posts e comentários...',
    'step5.explorer.filterAgent': 'Agente',
    'step5.explorer.filterPlatform': 'Plataforma',
    'step5.explorer.filterActionType': 'Tipo de ação',
    'step5.explorer.filterRound': 'Round',
    'step5.explorer.filterSuccess': 'Sucesso',
    'step5.explorer.clearFilters': 'Limpar filtros',
    'step5.explorer.resultsCount': '{count} ações encontradas',
    'step5.explorer.colRound': 'Round',
    'step5.explorer.colTime': 'Hora',
    'step5.explorer.colAgent': 'Agente',
    'step5.explorer.colPlatform': 'Plataforma',
    'step5.explorer.colAction': 'Ação',
    'step5.explorer.colContent': 'Conteúdo',
    'step5.explorer.colSuccess': 'Sucesso',
    'step5.explorer.prevPage': 'Anterior',
    'step5.explorer.nextPage': 'Próxima',
    'step5.explorer.pageInfo': 'Página {page} de {total} ({count} ações)',
    'step5.explorer.all': 'Todos',
    'step5.explorer.success': 'Sucesso',
    'step5.explorer.failure': 'Falha',
    'step5.explorer.noData': 'Nenhuma ação encontrada com os filtros atuais.',
    'step5.actions.types.CREATE_POST': 'Criar post',
    'step5.actions.types.LIKE_POST': 'Curtir',
    'step5.actions.types.QUOTE_POST': 'Citar',
    'step5.actions.types.REPOST_POST': 'Repostar',
    'step5.actions.types.CREATE_COMMENT': 'Comentar',
    'step5.actions.types.FOLLOW': 'Seguir',
    'common.loading': 'Carregando...',
    'common.unknownError': 'Erro desconhecido'
  }
  let text = translations[key] || key
  Object.entries(params).forEach(([k, v]) => {
    text = text.replace(`{${k}}`, String(v))
  })
  return text
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: tFn })
}))

const mockGetSimulation = vi.fn(() => Promise.resolve({ success: true, data: { total_rounds: 10, current_round: 5 } }))
const mockGetAgentStats = vi.fn(() => Promise.resolve({ success: true, data: { stats: [] } }))
const mockGetSimulationTimeline = vi.fn(() => Promise.resolve({ success: true, data: { timeline: [] } }))
const mockGetSimulationActions = vi.fn(() => Promise.resolve({ success: true, data: { actions: [], count: 0 } }))
const mockGetSimulationPosts = vi.fn(() => Promise.resolve({ success: true, data: { count: 0, posts: [] } }))

vi.mock('../../src/api/simulation.js', () => ({
  interviewAgents: vi.fn(() => Promise.resolve({ success: true, data: {} })),
  getSimulationProfilesRealtime: vi.fn(() => Promise.resolve({ success: true, data: { profiles: [] } })),
  getSimulation: (...args) => mockGetSimulation(...args),
  getAgentStats: (...args) => mockGetAgentStats(...args),
  getSimulationTimeline: (...args) => mockGetSimulationTimeline(...args),
  getSimulationActions: (...args) => mockGetSimulationActions(...args),
  getSimulationPosts: (...args) => mockGetSimulationPosts(...args),
}))

vi.mock('../../src/api/report.js', () => ({
  chatWithReport: vi.fn(() => Promise.resolve({ success: true, data: { response: 'hello' } })),
  getReport: vi.fn(() => Promise.resolve({ success: true, data: {} })),
  getAgentLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [] } })),
}))

vi.mock('../../src/utils/payloadValidator.js', () => ({
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

describe('Step5Interaction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  const mountComponent = (props = {}) => {
    return mount(Step5Interaction, {
      props: { reportId: 'r1', simulationId: 'sim1', ...props },
      global: { mocks: { $t: tFn } }
    })
  }

  it('renders overview cards with counts', async () => {
    mockGetSimulation.mockResolvedValue({ success: true, data: { total_rounds: 10, current_round: 5 } })
    mockGetAgentStats.mockResolvedValue({
      success: true,
      data: {
        stats: [
          { agent_id: 1, agent_name: 'Alice', total_actions: 50, twitter_actions: 30, reddit_actions: 20, action_types: { CREATE_POST: 20, LIKE: 15, COMMENT: 15 } },
          { agent_id: 2, agent_name: 'Bob', total_actions: 40, twitter_actions: 25, reddit_actions: 15, action_types: { CREATE_POST: 15, LIKE: 10, COMMENT: 15 } },
        ]
      }
    })
    mockGetSimulationActions.mockResolvedValue({ success: true, data: { count: 100, total: 100 } })
    mockGetSimulationPosts.mockResolvedValue({ success: true, data: { count: 25, total: 25 } })
    mockGetSimulationTimeline.mockResolvedValue({
      success: true,
      data: {
        timeline: [
          { round_num: 1, twitter_actions: 5, reddit_actions: 3, action_types: { CREATE_POST: 3, LIKE: 2, COMMENT: 3 } },
        ]
      }
    })

    const wrapper = mountComponent()
    await flushPromises()
    await nextTick()

    const cards = wrapper.findAll('.macro-card')
    expect(cards.length).toBe(6)

    // Verify labels
    const labels = cards.map(c => c.find('.macro-card-label').text())
    expect(labels).toContain('Agentes')
    expect(labels).toContain('Rounds')
    expect(labels).toContain('Ações')
    expect(labels).toContain('Posts')

    // Verify values
    const values = cards.map(c => c.find('.macro-card-value').text())
    expect(values).toContain('10')  // rounds from getSimulation
    expect(values).toContain('100') // actions from getSimulationActions
    expect(values).toContain('50')  // posts from getSimulationPosts (reddit 25 + twitter 25)
    expect(values).toContain('2')   // agents from getAgentStats
  })

  it('renders datagrid with actions', async () => {
    mockGetSimulation.mockResolvedValue({ success: true, data: { total_rounds: 10, current_round: 5 } })
    mockGetAgentStats.mockResolvedValue({ success: true, data: { stats: [] } })
    mockGetSimulationActions.mockImplementation((id, params) => {
      if (params?.limit === 1) {
        return Promise.resolve({ success: true, data: { count: mockActions.length, total: mockActions.length } })
      }
      return Promise.resolve({ success: true, data: { actions: mockActions, count: mockActions.length } })
    })
    mockGetSimulationPosts.mockResolvedValue({ success: true, data: { count: 0, posts: [] } })
    mockGetSimulationTimeline.mockResolvedValue({ success: true, data: { timeline: [] } })

    const wrapper = mountComponent()
    await flushPromises()
    await nextTick()

    // Switch to explore tab
    const tabs = wrapper.findAll('.dashboard-tab')
    const exploreTab = tabs.find(t => t.text().includes('Explorar'))
    expect(exploreTab).toBeDefined()
    await exploreTab.trigger('click')
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.explorer-table').exists()).toBe(true)
    expect(wrapper.findAll('.explorer-row').length).toBe(mockActions.length)
  })

  it('filters by platform', async () => {
    mockGetSimulation.mockResolvedValue({ success: true, data: { total_rounds: 10, current_round: 5 } })
    mockGetAgentStats.mockResolvedValue({ success: true, data: { stats: [] } })
    mockGetSimulationActions.mockImplementation((id, params) => {
      if (params?.limit === 1) {
        return Promise.resolve({ success: true, data: { count: mockActions.length, total: mockActions.length } })
      }
      return Promise.resolve({ success: true, data: { actions: mockActions, count: mockActions.length } })
    })
    mockGetSimulationPosts.mockResolvedValue({ success: true, data: { count: 0, posts: [] } })
    mockGetSimulationTimeline.mockResolvedValue({ success: true, data: { timeline: [] } })

    const wrapper = mountComponent()
    await flushPromises()
    await nextTick()

    // Switch to explore tab
    const tabs = wrapper.findAll('.dashboard-tab')
    const exploreTab = tabs.find(t => t.text().includes('Explorar'))
    await exploreTab.trigger('click')
    await flushPromises()
    await nextTick()

    // Select Twitter platform filter (second select is platform)
    const platformSelect = wrapper.findAll('.filter-select').at(1)
    await platformSelect.setValue('twitter')
    await nextTick()

    const rows = wrapper.findAll('.explorer-row')
    rows.forEach(row => {
      expect(row.text().toLowerCase()).toContain('twitter')
      expect(row.text().toLowerCase()).not.toContain('reddit')
    })
  })

  it('filters by agent', async () => {
    mockGetSimulation.mockResolvedValue({ success: true, data: { total_rounds: 10, current_round: 5 } })
    mockGetAgentStats.mockResolvedValue({ success: true, data: { stats: [] } })
    mockGetSimulationActions.mockImplementation((id, params) => {
      if (params?.limit === 1) {
        return Promise.resolve({ success: true, data: { count: mockActions.length, total: mockActions.length } })
      }
      return Promise.resolve({ success: true, data: { actions: mockActions, count: mockActions.length } })
    })
    mockGetSimulationPosts.mockResolvedValue({ success: true, data: { count: 0, posts: [] } })
    mockGetSimulationTimeline.mockResolvedValue({ success: true, data: { timeline: [] } })

    const wrapper = mountComponent()
    await flushPromises()
    await nextTick()

    // Switch to explore tab
    const tabs = wrapper.findAll('.dashboard-tab')
    const exploreTab = tabs.find(t => t.text().includes('Explorar'))
    await exploreTab.trigger('click')
    await flushPromises()
    await nextTick()

    // Select Alice agent filter (first select is agent)
    const agentSelect = wrapper.findAll('.filter-select').at(0)
    await agentSelect.setValue('Alice')
    await nextTick()

    const rows = wrapper.findAll('.explorer-row')
    expect(rows.length).toBeGreaterThan(0)
    rows.forEach(row => {
      expect(row.text()).toContain('Alice')
    })
  })

  it('renders empty state when no actions', async () => {
    mockGetSimulation.mockResolvedValue({ success: true, data: { total_rounds: 10, current_round: 5 } })
    mockGetAgentStats.mockResolvedValue({ success: true, data: { stats: [] } })
    mockGetSimulationActions.mockImplementation((id, params) => {
      if (params?.limit === 1) {
        return Promise.resolve({ success: true, data: { count: 0, total: 0 } })
      }
      return Promise.resolve({ success: true, data: { actions: [], count: 0 } })
    })
    mockGetSimulationPosts.mockResolvedValue({ success: true, data: { count: 0, posts: [] } })
    mockGetSimulationTimeline.mockResolvedValue({ success: true, data: { timeline: [] } })

    const wrapper = mountComponent()
    await flushPromises()
    await nextTick()

    // Switch to explore tab
    const tabs = wrapper.findAll('.dashboard-tab')
    const exploreTab = tabs.find(t => t.text().includes('Explorar'))
    await exploreTab.trigger('click')
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.explorer-empty').exists()).toBe(true)
    expect(wrapper.text()).toContain('Nenhuma ação encontrada')
  })
})

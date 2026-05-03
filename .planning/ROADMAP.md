# Roadmap: Quark

## Proposed Roadmap

**24 phases** | **20 requirements mapped** | All covered ✓

## Phases

- [x] **Phase 13: Dark Mode System** — Implement system-wide dark mode with CSS variables, toggle, and auto preference detection.
- [x] **Phase 14: Design System Refinements** — Evolve Blueprint Noir v2 tokens, audit components, standardize icons, and build a living style guide.
- [x] **Phase 15: Animations and Micro-interactions** — Add page transitions, hover/active feedback, skeleton loading, and progress indicators.
- [x] **Phase 16: Report Viewer Redesign** — Rebuild report layout with cards, interactive tables, mini-charts, and section navigation.
- [x] **Phase 17: Global UI Polish and Accessibility** — WCAG 2.1 AA audit, responsive refinements, console cleanup, and final consistency pass.

- [x] **Phase 22: Inventario Real do Estado Atual** — Baseline e Governanca. (completed 2026-05-01)
- [x] **Phase 23: Erros Visiveis e Seguros** — Estabilizacao Critica.
- [x] **Phase 24: Relatorios Confiaveis** — Estabilizacao Critica.
- [x] **Phase 25: Integridade Basica da Simulacao** — Estabilizacao Critica.
- [x] **Phase 26: Guardrails de Idioma** — Estabilizacao Critica.
- [x] **Phase 27: Contratos e Validacao** — Arquitetura e Resiliencia.
- [ ] **Phase 28: Services e Separacao de Camadas** — Arquitetura e Resiliencia.
- [ ] **Phase 29: Fallbacks** — Arquitetura e Resiliencia.
- [ ] **Phase 30: Observabilidade Operacional** — Arquitetura e Resiliencia.
- [ ] **Phase 31: Configuracao Assistida** — Experiencia do Workbench.
- [ ] **Phase 32: Controle de Execucao** — Experiencia do Workbench.
- [ ] **Phase 33: Grafo e Ontologia** — Experiencia do Workbench.
- [ ] **Phase 34: Relatorio Legivel** — Experiencia do Workbench.
- [x] **Phase 35: Dashboard de Inspecao** — Analytics e Qualidade de Dados. (completed 2026-05-02)
- [x] **Phase 36: Fidelidade do Grafo e Agentes** — Analytics e Qualidade de Dados. (completed 2026-05-02)
- [x] **Phase 37: Regressao por Cenario** — Analytics e Qualidade de Dados.
- [ ] **Phase 38: Preparacao de Beta** — Beta e Lancamento Controlado.
- [ ] **Phase 39: Feedback Loop** — Beta e Lancamento Controlado.
- [ ] **Phase 40: Pronto para Publico** — Beta e Lancamento Controlado.

## Phase Details

### Phase 13: Dark Mode System
**Goal**: Every screen renders correctly in light, dark, and auto modes via a token-driven CSS variable system.
**Depends on**: Phase 12 (completed)
**Requirements**: [DARK-01, DARK-02, DARK-03, DARK-04]
**Success Criteria** (what must be TRUE):
  1. User can toggle light/dark/auto and preference persists across sessions.
  2. All screens (auth, dashboard, simulation, graph, report, settings) show no visual regressions in either theme.
  3. Zero hardcoded hex/rgb colors in component styles — all via CSS custom properties.
  4. Auto mode reacts live to OS `prefers-color-scheme` changes.
**Plans**: 1 plan (13-01)

### Phase 14: Design System Refinements
**Goal**: Establish and apply Blueprint Noir v2 design tokens consistently across all reusable components.
**Depends on**: Phase 13
**Requirements**: [DSYS-01, DSYS-02, DSYS-03, DSYS-04]
**Success Criteria** (what must be TRUE):
  1. Token documentation exists and is discoverable in the running app (style guide).
  2. All target components match v2 specs for radius, shadow, focus, and disabled states.
  3. Single icon library is adopted and legacy icons are replaced.
  4. Developers can preview any token/component in both themes from the style guide.
**Plans**: 1 plan (14-01)

### Phase 15: Animations and Micro-interactions
**Goal**: The UI feels responsive and alive through purposeful motion and clear loading states.
**Depends on**: Phase 14
**Requirements**: [ANIM-01, ANIM-02, ANIM-03, ANIM-04]
**Success Criteria** (what must be TRUE):
  1. Route transitions are smooth and consistent (no flash of unstyled content).
  2. Every interactive element has visible hover, active, and focus states.
  3. Content-heavy loading areas use skeleton placeholders, not generic spinners.
  4. Long-running operations show progress (step labels or time estimates).
**Plans**: 1 plan (15-01)

### Phase 16: Report Viewer Redesign
**Goal**: Reports are scannable, visually rich, and easy to navigate with interactive data presentation.
**Depends on**: Phase 15
**Requirements**: [RPTV-01, RPTV-02, RPTV-03, RPTV-04]
**Success Criteria** (what must be TRUE):
  1. Report layout follows the 5-section due-diligence structure with clear visual hierarchy.
  2. Tables and mini-charts render inline for key metrics.
  3. Data source tags are accessible and visually distinct.
  4. Users can navigate long reports via anchor links or a floating outline.
**Plans**: 1 plan (16-01)

### Phase 17: Global UI Polish and Accessibility
**Goal**: The app meets professional accessibility and responsiveness standards with zero known UI drift.
**Depends on**: Phase 16
**Requirements**: [POLY-01, POLY-02, POLY-03, POLY-04]
**Success Criteria** (what must be TRUE):
  1. WCAG 2.1 AA contrast and keyboard requirements pass in both themes.
  2. Layout is usable from 320px to 1440px+ without horizontal scroll or broken grids.
  3. Dev build produces zero console warnings/errors related to UI.
  4. Consistency audit confirms 100% token adoption and no legacy style leakage.
**Plans**: 0 plans

### Phase 22: Inventario Real do Estado Atual
**Goal**: Inventario Real do Estado Atual — Estágio Baseline e Governanca do roadmap FUTUR.IA.
**Depends on**: Phase 21
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (22-01, 22-02, 22-03)

### Phase 23: Erros Visiveis e Seguros
**Goal**: Erros Visiveis e Seguros — Estágio Estabilizacao Critica do roadmap FUTUR.IA.
**Depends on**: Phase 22
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (23-01, 23-02, 23-03)

### Phase 24: Relatorios Confiaveis
**Goal**: Relatorios Confiaveis — Estágio Estabilizacao Critica do roadmap FUTUR.IA.
**Depends on**: Phase 23
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (24-01, 24-02, 24-03)

### Phase 25: Integridade Basica da Simulacao
**Goal**: Integridade Basica da Simulacao — Estágio Estabilizacao Critica do roadmap FUTUR.IA.
**Depends on**: Phase 24
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (25-01, 25-02, 25-03)

### Phase 26: Guardrails de Idioma
**Goal**: Guardrails de Idioma — Estágio Estabilizacao Critica do roadmap FUTUR.IA.
**Depends on**: Phase 25
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (26-01, 26-02)

### Phase 27: Contratos e Validacao
**Goal**: Contratos e Validacao — Estágio Arquitetura e Resiliencia do roadmap FUTUR.IA.
**Depends on**: Phase 26
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (27-01, 27-02)

### Phase 28: Services e Separacao de Camadas
**Goal**: Services e Separacao de Camadas — Estágio Arquitetura e Resiliencia do roadmap FUTUR.IA.
**Depends on**: Phase 27
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (28-01, 28-02, 28-03)

### Phase 29: Fallbacks
**Goal**: Fallbacks — Estágio Arquitetura e Resiliencia do roadmap FUTUR.IA.
**Depends on**: Phase 28
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (29-01, 29-02, 29-03)

### Phase 30: Observabilidade Operacional
**Goal**: Observabilidade Operacional — Estágio Arquitetura e Resiliencia do roadmap FUTUR.IA.
**Depends on**: Phase 29
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (30-01, 30-02)

### Phase 31: Configuracao Assistida
**Goal**: Configuracao Assistida — Estágio Experiencia do Workbench do roadmap FUTUR.IA.
**Depends on**: Phase 30
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (31-01, 31-02, 31-03)

### Phase 32: Controle de Execucao
**Goal**: Controle de Execucao — Estágio Experiencia do Workbench do roadmap FUTUR.IA.
**Depends on**: Phase 31
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (32-01, 32-02, 32-03)

### Phase 33: Grafo e Ontologia
**Goal**: Grafo e Ontologia — Estágio Experiencia do Workbench do roadmap FUTUR.IA.
**Depends on**: Phase 32
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (33-01, 33-02)

### Phase 34: Relatorio Legivel
**Goal**: Relatorio Legivel — Estágio Experiencia do Workbench do roadmap FUTUR.IA.
**Depends on**: Phase 33
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (34-01, 34-02)

### Phase 35: Dashboard de Inspecao
**Goal**: Dashboard de Inspecao — Estágio Analytics e Qualidade de Dados do roadmap FUTUR.IA.
**Depends on**: Phase 34
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (35-01, 35-02, 35-03)

### Phase 36: Fidelidade do Grafo e Agentes
**Goal**: Fidelidade do Grafo e Agentes — Estágio Analytics e Qualidade de Dados do roadmap FUTUR.IA.
**Depends on**: Phase 35
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (36-01, 36-02, 36-03)

### Phase 37: Regressao por Cenario
**Goal**: Regressao por Cenario — Estágio Analytics e Qualidade de Dados do roadmap FUTUR.IA.
**Depends on**: Phase 36
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (37-01, 37-02, 37-03)

### Phase 38: Preparacao de Beta
**Goal**: Preparacao de Beta — Estágio Beta e Lancamento Controlado do roadmap FUTUR.IA.
**Depends on**: Phase 37
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (38-01, 38-02, 38-03)

### Phase 39: Feedback Loop
**Goal**: Feedback Loop — Estágio Beta e Lancamento Controlado do roadmap FUTUR.IA.
**Depends on**: Phase 38
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 2 plans executados e verificados.
**Plans**: 2 plan(s) (39-01, 39-02)

### Phase 40: Pronto para Publico
**Goal**: Pronto para Publico — Estágio Beta e Lancamento Controlado do roadmap FUTUR.IA.
**Depends on**: Phase 39
**Requirements**: [TBD]
**Success Criteria** (what must be TRUE):
  1. Gate de saida do épico atingido.
  2. Todos os 3 plans executados e verificados.
**Plans**: 3 plan(s) (40-01, 40-02, 40-03)

## Progress

**Execution Order:**
Phases execute in numeric order: 13, 14, 15, 16, 17

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 13. Dark Mode System | 1/1 | Complete | 2026-04-28 |
| 14. Design System Refinements | 1/1 | Complete | 2026-04-28 |
| 15. Animations and Micro-interactions | 1/1 | Complete | 2026-04-28 |
| 16. Report Viewer Redesign | 1/1 | Complete | 2026-04-28 |
| 17. Global UI Polish and Accessibility | 1/1 | Complete | 2026-04-28 |
| 22. Inventario Real do Estado Atual | 0/3 | Complete    | 2026-05-01 |
| 23. Erros Visiveis e Seguros | 3/3 | Complete | 2026-05-01 |
| 24. Relatorios Confiaveis | 1/3 | In Progress | — |
| 25. Integridade Basica da Simulacao | 0/3 | In Progress | — |
| 26. Guardrails de Idioma | 0/2 | Planned | — |
| 27. Contratos e Validacao | 0/2 | Planned | — |
| 28. Services e Separacao de Camadas | 0/3 | Planned | — |
| 29. Fallbacks | 0/3 | Planned | — |
| 30. Observabilidade Operacional | 0/2 | Planned | — |
| 31. Configuracao Assistida | 0/3 | Planned | — |
| 32. Controle de Execucao | 0/3 | Planned | — |
| 33. Grafo e Ontologia | 0/2 | Planned | — |
| 34. Relatorio Legivel | 0/2 | Planned | — |
| 35. Dashboard de Inspecao | 0/3 | Planned | — |
| 36. Fidelidade do Grafo e Agentes | 0/3 | Planned | — |
| 37. Regressao por Cenario | 0/3 | Planned | — |
| 38. Preparacao de Beta | 0/3 | Planned | — |
| 39. Feedback Loop | 0/2 | Planned | — |
| 40. Pronto para Publico | 0/3 | Planned | — |
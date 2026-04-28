# Development

## Repo layout

```text
.
├── frontend/                 # Vue 3 + Vite client
│   ├── src/api/             # frontend API wrappers and auth stub
│   ├── src/components/      # reusable UI
│   ├── src/router/          # route table + guards
│   ├── src/store/           # lightweight local state
│   ├── src/views/           # route-level screens
│   └── vite.config.js       # dev server + proxy config
├── backend/                 # Flask backend
│   ├── app/api/            # graph, simulation, report, research blueprints
│   ├── app/models/         # local persistence models
│   ├── app/services/       # business logic and external integrations
│   ├── app/utils/          # config, locale, logging, helpers
│   ├── scripts/            # simulation helper scripts
│   └── tests/              # backend pytest suites
├── docs/                   # project docs
├── .github/workflows/      # CI workflows
├── Dockerfile
├── docker-compose.yml
└── package.json
```

## Day-to-day commands

From the repo root:

```bash
# install everything
npm run setup:all

# run frontend + backend together
npm run dev

# frontend production build
npm run build

# reporting contamination checks
npm run preflight
```

From `backend/`:

```bash
uv run pytest
```

## Frontend development notes

### Tooling

- Vue 3
- Vue Router
- Vue I18n
- Vite
- Axios
- D3

### Route structure

Committed route components:

- `Home.vue`
- `LoginPage.vue`
- `RegisterPage.vue`
- `MainView.vue`
- `SimulationView.vue`
- `SimulationRunView.vue`
- `ReportView.vue`
- `InteractionView.vue`

### Frontend API modules

`frontend/src/api/` currently contains:

- `auth.js`
- `graph.js`
- `report.js`
- `research.js`
- `simulation.js`
- `index.js`

### Auth caveat

The frontend auth layer is not server-backed in the committed repo. `frontend/src/api/auth.js` stores a mock user in localStorage and drives route access that way.

If you touch login/register flows, document clearly whether you are still working with the stub or introducing a real backend session/auth system.

## Backend development notes

### Tooling

- Flask application factory pattern
- dotenv-backed config loading
- daemon-thread background tasks for long-running work
- local file persistence under `backend/uploads/`

### Main backend blueprints

- `graph.py` — project, ontology, graph build, tasks, graph data
- `simulation.py` — entity access, preparation, run lifecycle, interviews, timeline data
- `report.py` — report generation, retrieval, logs, sections, report chat
- `research.py` — deep research start/status/result/approve/reject/promote/rerun

### Health endpoint

The backend app factory exposes:

```text
GET /health
```

### Observability

Observability is wired at app startup and exercised in backend tests. If you change service lifecycles or startup wiring, check the observability tests under `backend/tests/`.

## Research and graph workflow notes

There is a clear research-only path in the codebase:

1. start a research run
2. approve it
3. promote it into a project or create a new project from it
4. generate ontology from extracted text
5. preview/build the graph

The backend tests cover that path explicitly.

## Documentation expectations

When changing behavior that affects users or contributors, update:

- `README.md`
- docs under `docs/`
- `CONTRIBUTING.md` if contribution workflow changes

## Before opening a PR or handing off work

At minimum, run the commands relevant to your change set:

```bash
npm run build
cd backend && uv run pytest
npm run preflight
```

Use judgment:

- UI-only change -> at least `npm run build`
- backend behavior change -> backend pytest
- reporting/persistence contamination change -> `npm run preflight`

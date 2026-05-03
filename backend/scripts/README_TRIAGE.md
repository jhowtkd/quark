# Triagem Semanal de Feedback

Este documento descreve o pipeline de triagem semanal de feedback beta do FUTUR.IA.

## Comando

```bash
cd backend && uv run python -m scripts.weekly_triage --since YYYY-MM-DD [--auto-classify] [--generate-backlog] [--generate-changelog] [--dry-run]
```

## Exemplo completo

```bash
cd backend && uv run python -m scripts.weekly_triage \
  --since 2026-04-24 \
  --auto-classify \
  --generate-backlog \
  --generate-changelog
```

## Heurísticas de Auto-classificação

| Condição | Severidade |
|---|---|
| `rating == 1` e `category == "bug"` | P0 (bloqueio) |
| `rating == 2` e `category == "bug"` | P1 (grave) |
| `rating <= 3` e `category == "ux_confusion"` | P2 (médio) |
| `category == "suggestion"` | P3 (leve) |
| `rating >= 4` | P3 (leve — feedback positivo) |

## Severidades

- **P0** — Bloqueio: impede o uso da funcionalidade
- **P1** — Grave: funcionalidade quebrada com workaround
- **P2** — Médio: UX ruim ou lentidão
- **P3** — Leve: sugestão ou polish

## Artefatos Gerados

### Backlog
- Local: `backend/uploads/feedback/backlog/backlog-YYYY-MM-DD.jsonl`
- Formato: uma linha JSON por item
- Contém apenas itens P0/P1

### Changelog
- Local: `docs/changelogs/beta-YYYY-MM-DD.md`
- Formato: Markdown com seções por severidade
- Inclui agradecimentos aos testers

## Fluxo Recomendado para o Operador

1. **Executar auto-classificação** para classificar feedbacks não triados
2. **Revisar P0/P1** manualmente antes de converter em backlog
3. **Gerar backlog** para criar tarefas rastreáveis
4. **Gerar changelog** para comunicar aos testers

## Dashboard Web

Acesse `/admin/triage` no frontend para triagem manual via interface web.

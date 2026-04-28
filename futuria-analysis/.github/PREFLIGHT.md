# Preflight Checks

## Language Contamination Gates

These gates detect forbidden-script (CJK, Cyrillic, fullwidth, etc.) regressions in reporting-critical surfaces.

### Quick Reference

```bash
# Full preflight (recommended before commits)
npm run preflight

# Individual checks
npm run check:language-backend    # Backend surfaces must be clean
npm run check:language-artifacts # Persisted artifacts scan
npm run check:language-reporting # Full reporting scope (policy-relative)
```

### Backend Surfaces (CI Gate)

Checks that the following files remain clean (no forbidden scripts):

- `backend/app/services/report_agent.py`
- `backend/app/services/zep_tools.py`
- `backend/app/api/report.py`
- `backend/app/utils/locale.py`
- `backend/app/utils/language_integrity.py`

```bash
python3 scripts/check_language_contamination.py --scope reporting-backend --fail-on-policy-breach
```

### Persisted Artifacts Scan

Scans persisted report artifacts for contamination:

```bash
python3 scripts/normalize_report_artifacts.py --scope reporting --dry-run --fail-on-contamination
```

### Policy Baselines

The `reporting` scope in `config/language_policy.json` tracks both:
- Files expected to be dirty (historical contamination)
- Files expected to be clean (enforcement targets)

The `reporting-backend` scope is the enforcement baseline for CI.

## GitHub Actions

The `language-contamination-gate.yml` workflow runs on:

- Pull requests modifying reporting-critical files
- Pushes to `main` and `develop` branches
- Manual trigger via `workflow_dispatch`

## Troubleshooting

### "Expected=True actual=False" Breach

This means a file was cleaned but the policy still marks it as expected dirty. Update `config/language_policy.json`:

```json
{
  "path": "backend/app/services/report_agent.py",
  "expected_contamination": false
}
```

### New Contamination Detected

If new forbidden scripts appear in clean files:

1. Run `npm run remediate:report-artifacts` to see what needs attention
2. Apply `npm run remediate:report-artifacts:fix` for automatic remediation
3. Or quarantine manually: `python3 scripts/normalize_report_artifacts.py --scope reporting --quarantine`

# Beta Privacy Pre-Release Checklist

This checklist must be completed and signed off before any beta release of FUTUR.IA. All items are mandatory.

---

## 1. Repository

- [ ] **1.1 `.gitignore` covers `.env` and `.env.beta`** — Verify that no `.env*` files are tracked by git.
  - Verification: `git ls-files | grep -E '^\.env' && echo "FAIL" || echo "PASS"`

- [ ] **1.2 `scan_secrets` passes without findings** — Run the secrets scanner and confirm no keys or tokens are present in source files.
  - Verification: `python3 scripts/scan_secrets.py`

- [ ] **1.3 No tracked uploads or logs** — Ensure `backend/uploads/`, `backend/logs/`, and their subdirectories are never committed.
  - Verification: `git ls-files | grep -E 'backend/(uploads|logs)/' && echo "FAIL" || echo "PASS"`

- [ ] **1.4 No hardcoded API keys or credentials** — Review codebase for literal keys, passwords, or certificate material.
  - Verification: `grep -rEn '(sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,}|api[_-]?key\s*=\s*["\x27][^"\x27]{10,})' backend/app/ --include='*.py' || echo "PASS"`

---

## 2. Tester Data

- [ ] **2.1 Uploads limited to 50 MB and allowed extensions** — Confirm `MAX_CONTENT_LENGTH` and `ALLOWED_EXTENSIONS` are enforced in all upload handlers.
  - Verification: `grep -n 'MAX_CONTENT_LENGTH\|ALLOWED_EXTENSIONS' backend/app/config.py`

- [ ] **2.2 Logs are sanitized** — PII (email, CPF, phone) must be redacted from INFO+ log messages when `LOG_SANITIZE=true`.
  - Verification: `grep -n 'LOG_SANITIZE' .env.beta.example`

- [ ] **2.3 Post content is truncated in logs** — Long user-generated posts must be truncated before logging to avoid full content leakage.
  - Verification: Review `backend/app/` logging calls for truncation patterns (e.g., `[:200]`).

- [ ] **2.4 Test datasets are 100% fictional** — All seeded data, personas, and simulation inputs used in beta must be synthetic. No real user data.
  - Verification: Manual review of `backend/tests/fixtures/` and seed scripts.

---

## 3. Traces and Observability

- [ ] **3.1 Langfuse disabled by default in beta** — The beta `.env` example must set `LANGFUSE_ENABLED=false`.
  - Verification: `grep '^LANGFUSE_ENABLED=' .env.beta.example`

- [ ] **3.2 Sample rate ≤ 20% if Langfuse is enabled in beta** — When `LANGFUSE_ENABLED=true` and `LANGFUSE_ENV=beta`, `LANGFUSE_SAMPLE_RATE` must be `<= 0.2`.
  - Verification: `cd backend && uv run pytest tests/config/test_langfuse_beta_restriction.py -v`

- [ ] **3.3 Traces do not contain PII** — Confirm that trace payloads exclude emails, names, CPF, phone numbers, and addresses before sending to Langfuse.
  - Verification: Review Langfuse decorator/wrapper code for sanitization filters.

- [ ] **3.4 No traceback in HTTP responses** — Flask must be configured to return generic error messages; stack traces must never reach the client.
  - Verification: `grep -n 'PROPAGATE_EXCEPTIONS\|DEBUG' backend/app/config.py` and confirm production-like settings.

---

## 4. Exports and Access

- [ ] **4.1 Endpoints validate ownership or document gap** — Every export or data-retrieval endpoint must check that the requesting user owns the resource, or the gap must be explicitly documented in `docs/SECURITY-GAPS.md`.
  - Verification: Audit `backend/app/routes/` for `@require_auth` or ownership checks on download/export endpoints.

- [ ] **4.2 Exports exclude `llm_raw_response`, `prompt_text`, and `traceback`** — Report and simulation exports must strip internal LLM artifacts and exception details.
  - Verification: Review serialization logic in report and simulation services for exclusion of `llm_raw_response`, `prompt_text`, and `traceback` fields.

- [ ] **4.3 Reports do not expose thinking process** — Internal reasoning, chain-of-thought, or reflection steps must be omitted from user-facing report outputs.
  - Verification: Manual review of report generation templates and JSON schemas.

- [ ] **4.4 Feedback stored separately from simulation data** — User feedback (ratings, comments) must reside in a distinct table or collection from simulation states and raw results.
  - Verification: Review database schema or storage layout to confirm feedback isolation.

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Security Lead | | | |
| Backend Lead | | | |
| Privacy Officer | | | |
| Release Manager | | | |

# SETUP.md — Aegis local setup

> Canonical setup guide (verified 2026-10-13 against this worktree).
> Shell: **Windows PowerShell 5.1**. Commands below use PowerShell syntax.
> Summary version: `docs/LOCAL_SETUP.md`.

---

## 1. Prerequisites

| Requirement | Version | Install / notes |
|---|---|---|
| Python | 3.11.x (`python --version`) | https://python.org or `pyenv install 3.11` |
| uv | latest (`uv --version`) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (or `irm … \| iex` on Windows) |
| Git | any | https://git-scm.com |
| Docker Desktop | any recent (WSL2 backend) | **Required only for sandbox execution + integration proofs.** Without a daemon the sandbox fail-closes (`Error(governance_unavailable)`); proofs skip cleanly. |
| PostgreSQL | **not required separately** | `pgserver` bundles Postgres 16; tests + CLI auto-start it. Set `WARDEN_PG_URI` only to use your own server. |

---

## 2. Clone and install

```powershell
git clone https://github.com/parth5012/warden
cd warden
uv sync --extra dev
```

Verify the kernel imports (PowerShell needs `$env:` — bare `PYTHONPATH=src`
does **not** work here):

```powershell
$env:PYTHONPATH='src'
uv run python -c "import warden.executor, warden.journal, warden.policy.engine, warden.grants; print('kernel OK')"
```

---

## 3. Configure environment

```powershell
Copy-Item .env.example .env
notepad .env
```

| Variable | Required? | Purpose |
|---|---|---|
| `GROQ_API_KEY` / `GROQ_MODEL` | For governed chat | Groq inference (`openai/gpt-oss-20b` default). Chat + drafting stay inert without it. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Optional | Alternate LLM providers via `src/warden/llm/providers.py`. |
| `WARDEN_APPROVER_KEYS` | For approvals | Named keys, e.g. `admin:aegis-secret-key-123` or `alice:k1,bob:k2`. Sent as approver header; recorded in journal. Demo auth, not real auth. |
| `WARDEN_PG_URI` (aliases: `CONNECTION_STRING`, `DATABASE_URL`, `POSTGRES_URI`) | Optional | External Postgres. Omit → bundled `pgserver` starts automatically. |
| `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` (`CLEF_*` aliases work) | Optional | Live L2 (Clef) judgments. **Unset → hermetic `FakeClefClient`, no network.** Outage fail-closes. |
| `WARDEN_SANDBOX_WORKSPACE` | Optional | Host dir bind-mounted into the container (default `D:/tmp` on Windows, `/tmp` elsewhere). Created if missing. |
| `WARDEN_SANDBOX_IMAGE` | Optional | Container image override (default pinned `alpine@sha256:…` in `src/warden/sandbox/registry.py`). |
| `GATE_DENY_THRESHOLD` / `GATE_CLEAN_THRESHOLD` | Optional | L1/L2 score bands (defaults `0.85` / `0.20`; between → escalate). |

Settings load from `backend/.env`, `.env`, `src/warden/.env`, `./.env`
(see `src/warden/config.py`).

---

## 4. Run tests

```powershell
$env:PYTHONPATH='src'
uv run pytest -q
```

- Baseline 2026-10-13: **217+ tests collectible across 40 modules**
  (executor, policy gate, grants + e2e, HITL approvals, sandbox unit +
  Docker integration proofs, LLM client, golden evals, chat/panels).
- ~20 app/backend modules additionally need `psycopg`, `sqlglot`,
  `langgraph-checkpoint-postgres` — a clean `uv sync --extra dev` provides
  them. If you see `ModuleNotFoundError: No module named 'warden'`, you
  forgot `$env:PYTHONPATH='src'`.
- Docker integration proofs (`tests/test_sandbox_integration.py`) prove
  network-none, read-only rootfs, timeout kill, zero leftover containers —
  and skip cleanly when no daemon is available.

Typecheck (strict, covers `src`, `tests`, `backend`, `frontend`):

```powershell
$env:PYTHONPATH='src'
uv run mypy src tests
```

---

## 5. Run the web console

```powershell
$env:PYTHONPATH='src'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://localhost:8000`:

| Route | What |
|---|---|
| `/` | Dashboard — live journal, telemetry, pending gates, runs |
| `/approvals` | Approval triage queue (HTMX) |
| `/chat` | Governed OpsAssistant chat |
| `/grants` | Issue / list / revoke task-scoped grants |
| `/audit`, `/policies`, `/traces`, `/sandbox`, `/llm` | Audit explorer, policy viewer, traces, sandbox runs, LLM usage |
| `/actions/{id}` | Blast-radius review for a proposed action |
| `/api/*` | JSON API: `runs`, `inbox`, `audit`, `telemetry`, `policies`, `llm`, `auth`, `health` |

Launch a run from the dashboard prompt, or:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/runs `
  -ContentType 'application/json' -Body '{"prompt":"Weekly ops report ready"}'
```

---

## 6. Run the CLI harness (park/resume demo)

```powershell
$env:PYTHONPATH='src'
uv run python tests/cli_chat.py
# /state /history /new /resume /quit ; plain text sends graph input
# parked threads auto-prompt for a resume decision on rejoin
uv run python tests/cli_chat.py --thread <thread-id>   # crash-recovery demo
```

---

## 7. Try the four core beats

1. **Telemetry** — chat or launch a run; dashboard cards fill (tokens, cost, latency per call, all journal projections).
2. **Gate** — trigger an email-send-class escalate → `Pending` → approve in
   `/approvals` as a named approver → timeline shows
   `requested → decided(approve, alice) → completed`.
3. **Deny** — attempt unbounded destruction (`DROP DATABASE`, multi-statement
   / `CASCADE` DDL, unconfined `rm -rf /`, `/etc/shadow`, `..` traversal) →
   terminal `Denied`, red card, **not approvable**.
4. **Sandbox + grants** — `rm -rf` runs Docker-contained
   (`--network=none`, RO rootfs, 30s/256m/1cpu); bounded ops
   (`DROP TABLE <name>`, `/workspace/tmp/` batch delete) escalate but
   auto-allow when covered by a live grant.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'warden'` | `$env:PYTHONPATH='src'` before every `uv run` (PowerShell syntax). |
| `No module named 'psycopg' / 'sqlglot' / 'langgraph.checkpoint.postgres'` | Stale/partial venv → `uv sync --extra dev` fresh; re-run with `PYTHONPATH=src`. |
| `pgserver fails to start` | `uv run python -c "import pgserver; print('ok')"`; wipe temp dir (`Remove-Item -Recurse $env:TEMP\warden-pg-*`); retry. Or set `WARDEN_PG_URI` to your own Postgres. |
| `uv sync` fails | `python --version` must be 3.11.x; `uv cache clean`; retry. |
| Sandbox → `Error(governance_unavailable)` | Docker daemon down / image missing / unknown tool profile — fail-closed by design. Start Docker Desktop, or test kernel paths (executor/policy/grants) which don't need it. |
| LLM chat inert | Set `GROQ_API_KEY` (and optionally `GROQ_MODEL`). Without it, drafting/clients stay unconfigured and calls fail closed. |
| Clef L2 never fires live | Set `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN`; otherwise `FakeClefClient` is used (offline-safe). |
| `CompiledStateGraph` mypy errors | Annotate `CompiledStateGraph[Any, Any, Any, Any]` (see `docs/DEVELOPMENT_GUIDE.md`). |
| `from tests import cli_chat` fails | `tests/__init__.py` must exist; don't add `mypy_path`. |

---

## 9. What is intentionally not here

- No login system (named keys only — lock 8).
- No `DENY` override (edit the versioned policy instead — lock 5).
- No subprocess sandbox (Docker-only since DECISIONS.md #1).
- No Postgres migration step yet (bundled `pgserver` + SQLite approvals carry
  local dev; full Postgres + pgvector migration is tracked hardening work).

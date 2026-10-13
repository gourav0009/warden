# STATUS.md — Aegis: What's Built

> Last updated: 2026-10-13 — resynced with codebase (executor, journal, policy L0/L1/L2, grants, Docker sandbox, FastAPI + backend API, agent engine all present; 40 test modules, 217+ collectible tests).

---

## Overall Progress

| Phase | Name | Status |
|---|---|---|
| 0 | Foundation | ✅ Done |
| 1 | Core story (single ops-assistant agent) | ✅ Largely built (executor, journal, policy, HITL, Docker sandbox, FastAPI, ops-assistant all present; hardening ongoing) |
| 2 | Policy as a product | ⬜ Not started |
| 3 | Multi-agent | ⬜ Not started |
| 4 | Explainability polish | ⬜ Not started |

---

## What's Actually Built

### ✅ Project scaffold
- `pyproject.toml` — uv-managed, Python 3.11, direct deps declared (`psycopg-pool`, `langchain-core`, `typing-extensions`)
- `src/warden/` package, `tests/` package (both with `__init__.py`)
- `.gitignore`, `.python-version`

---

### ✅ `src/warden/models.py`
Core domain types:
- `Action` — unit that crosses the executor seam (`kind ∈ {tool, llm}`, `name`, `payload`, `run_id`, `thread_id`)
- `Outcome` — `Allowed` | `Denied` | `Pending` | `Error`
- Gate types (`GateRequest`, `GateDecision`)
- `CheckpointInfo` — view type for checkpoint state inspection

---

### ✅ `src/warden/checkpoint.py` — `CheckpointManager`
The deep module for LangGraph checkpoint infrastructure:

| Feature | Detail |
|---|---|
| `create(conn_string)` | Async context manager, owns `AsyncPostgresSaver` lifecycle; idempotent setup on every boot |
| `health_check()` | Probes connection (handles both connection and pool) |
| `get_state_info()` | Logged state inspection, **fail-closed** → `Error("governance_unavailable")`, never raises |
| `get_state_history()` | Returns oldest-first ordered history (reversed from LangGraph default newest-first) |
| `resume(graph, config, value)` | Logging wrapper around `graph.ainvoke(Command(resume=...))`, fail-closed |
| Connection string redaction | `_redact()` — masks URI userinfo **and** keyword-DSN `password=...` form; urlsplit-based |

---

### ✅ `src/warden/demo_graph.py`
Draft demo LangGraph graph:
- Three-node flow: `draft → interrupt(approval) → send/abort`
- Proves park/resume mechanics with the checkpointer

---

### ✅ `tests/conftest.py`
- Session-scoped real-PostgreSQL fixture (via bundled `pgserver`, no root required)

---

### ✅ `tests/test_checkpoint.py` — 12 tests vs real Postgres
Covers:
- Idempotent setup
- Park/resume (approve + deny paths)
- No duplicate output on resume
- **Manager-restart recovery** (crash-and-rejoin)
- History walk (asserts non-decreasing step order)
- Fail-closed after close (`state`, `history`, `resume` all return `Error`)
- Bad-connection startup failure
- `_redact` — 6-case parametrize (URI form, keyword-DSN, `@` in query string, etc.)

---

### ✅ `tests/cli_chat.py` — CLI chat harness
Reusable interactive CLI for any compiled LangGraph graph:

| Command | Behaviour |
|---|---|
| `/state` | Print current checkpoint state |
| `/history` | Walk all checkpoint steps |
| `/new` | Start a new thread |
| `/resume` | Manually trigger resume |
| `/quit` | Exit cleanly (no traceback on EOF/Ctrl-C) |
| _(parked thread on rejoin)_ | Auto-detects park, prompts for resume decision |

- Auto-starts bundled `pgserver`; `--pg` / `WARDEN_PG_URI` to override
- Server intentionally left running so restart-and-resume is demoable
- `/quit` at the `resume>` prompt exits cleanly without treating it as a decision value (bug fix)

---

### ✅ `tests/test_cli_chat.py` — 4 regression tests
- `/quit` at resume prompt → thread stays parked
- Empty re-prompt stays in prompt loop
- Failed resume → re-prompts (doesn't route as decision)
- Re-park loop re-prompts correctly

---

## Key Design Decisions Locked In

| Lock | Decision |
|---|---|
| 1 | Both tool and LLM calls cross the executor seam |
| 2 | `execute()` returns `Pending` explicitly — no transparent interrupt inside it |
| 3 | Write-ahead + checkpointer division of labour: journal = evidence, checkpointer = control-flow |
| 4 | Fail-closed everywhere — `execute()` never raises for environmental reasons |
| 5 | DENY is terminal — no human override of a policy deny |
| 7 | One sandbox port, adapter routes itself |
| 8 | Approver identity = named keys in env |
| 9 | Policies live in DB (`policy_versions` append-only) |
| 10 | Single ops-assistant agent first, then expand |
| 11 | Product name = **Aegis** |
| 12 | UI = Jinja + HTMX, server-rendered in FastAPI, JSON-clean endpoints |

---

## What's NOT Built Yet (remaining hardening)

- Postgres-backed `AuditJournal` persistence + pgvector policy retrieval (in-memory + SQLite approvals + file-backed grants are live; Postgres WAL/audit decorators landed, full migration still pending)
- Policy CRUD UI polish + live rule-edit demo (engine + versions design done, editor UX partial)
- Multi-agent leaderboard / run-comparison views (agent registry + second agent present, comparison views partial)
- Decision-graph / run-replay UI polish (projections + timeline present, polish pending)

Previously listed here but NOW BUILT (verified 2026-10-13): `GuardedExecutor` (`src/warden/executor.py`), `AuditJournal` (`src/warden/journal.py` — hash-chained, idempotent, secret-redacting), `PolicyEngine` (`src/warden/policy/engine.py` — L0 static + L1 DeBERTa + L2 Clef), HITL re-entry + durable approvals (`src/warden/hitl/approvals.py`, `app/` + `backend/api/inbox.py`), `SandboxPort` Docker adapter (`src/warden/sandbox/docker.py` + `registry.py` + `port.py`), LLM client adapter (`src/warden/llm/` — budget, pricing, rate-limit, Groq/OpenAI), projections (`src/warden/projections/`), FastAPI app (`app/main.py` + `backend/api/`) with dashboard/approvals/chat/grants/policies/sandbox/traces endpoints, ops-assistant + multi-agent engine (`src/warden/agent_engine.py`, `src/warden/tools/`), user grants (`src/warden/grants.py`, `app/grants.py`).

---

## Test & Quality Status

```
pytest   →  217+ collectible tests across 40 modules (kernel: executor/policy/grants/HITL/sandbox/LLM all covered; app/backend integration covered where deps installed)
mypy     →  strict mode over src, tests, backend, frontend (see pyproject.toml)
```

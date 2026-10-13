# Aegis — AI Agent Governance & Human Accountability

> **Every LLM call and tool call crosses one seam. Nothing downstream can be skipped.**

Aegis is a governance layer that LangGraph-based agents run *through*. Every
action is journaled, checked against policy, sandboxed, and — when policy is
unsure — parked for human approval before any side effect takes place.

Docs resynced with the codebase on **2026-10-13** (verified: executor,
journal, L0/L1/L2 policy, grants, Docker sandbox, FastAPI + backend API,
agent engine all present).

---

## The seam

```python
outcome = await executor.execute(action, ctx)
# -> Allowed(result) | Denied(reason, policy) | Pending(gate_request) | Error(reason)
```

| Outcome | Meaning |
|---|---|
| `Allowed(result)` | Passed policy (or approved / grant-covered) and executed |
| `Denied(reason, policy)` | Blocked by policy — **terminal, no human override** |
| `Pending(gate_request)` | Escalated — human approval required before execution |
| `Error(reason)` | Governance failure — fail-closed, action not executed |

Rules: `execute()` never raises for environmental reasons (only bugs raise).
`Pending` is data, never an exception. `DENY` can never be overridden —
not by approvers, not by grants.

---

## How it fits together

```
Agent graph (LangGraph: demo_graph + agent_engine OpsAssistant)
        │
        ▼
GuardedExecutor (src/warden/executor.py)          ◄── the single seam
 ├── AuditJournal (src/warden/journal.py)          hash-chained, idempotent, secret-redacting
 ├── PolicyEngine (src/warden/policy/)             L0 static AST → L1 DeBERTa → L2 Clef
 ├── Grants (src/warden/grants.py)                 task-scoped user capabilities (escalate path only)
 ├── HITL approvals (src/warden/hitl/approvals.py) durable store, one-time claim, fingerprint binding
 ├── SandboxPort (src/warden/sandbox/)             Docker containment (--network=none, RO rootfs, 30s/256m/1cpu)
 └── LLM client (src/warden/llm/)                  budget, pricing, rate-limit, Groq/OpenAI, usage → journal
        │
        ▼
FastAPI console (app/main.py) + JSON API (backend/api/)
 ├── Dashboard `/` — live journal, telemetry, pending gates, runs
 ├── Approvals `/approvals` + inbox API — park → approve/deny → resume
 ├── Chat `/chat` — governed OpsAssistant (Groq default)
 ├── Grants `/grants` — issue / list / revoke capabilities
 ├── Audit / policies / traces / sandbox / llm views
 └── Blast-radius `GET /actions/{id}` — proposed-action impact review
```

Dependency rule: `src/warden/` never imports from `app/`, `backend/`, or
`frontend/`. The kernel is a library; the web layers are callers.

---

## What is built (verified 2026-10-13)

| Area | Location | State |
|---|---|---|
| GuardedExecutor | `src/warden/executor.py` | ✅ write-ahead → policy → grant/approval → handler → journal |
| AuditJournal | `src/warden/journal.py` | ✅ hash chain, `(run_id, action_id, kind)` idempotency, redaction |
| Policy L0/L1/L2 | `src/warden/policy/` | ✅ sqlglot/bashlex/path rules, DeBERTa scorer, Clef client + fake fallback |
| User grants | `src/warden/grants.py`, `app/grants.py` | ✅ scoped DDL + `/workspace/tmp/` batch-delete, TTL + max-uses, revoke |
| HITL + inbox | `src/warden/hitl/approvals.py`, `backend/api/inbox.py` | ✅ SQLite durable store, replay/expiry/auth binding |
| Docker sandbox | `src/warden/sandbox/` | ✅ exec/shell profiles, argv-built `docker`, fail-closed `SandboxUnavailable` |
| LLM client | `src/warden/llm/` | ✅ budget/reservation, pricing, tokenizer, Groq/OpenAI adapters |
| Agent engine | `src/warden/agent_engine.py`, `src/warden/tools/` | ✅ OpsAssistant + registry, safe/deny/hitl/sandbox toolsets, Groq drafting |
| Web console + API | `app/`, `backend/api/`, `frontend/` | ✅ dashboard, approvals, chat, grants, audit, policies, traces, sandbox, llm |
| Checkpointing | `src/warden/checkpoint.py` | ✅ LangGraph saver lifecycle, park/resume, fail-closed inspection |
| Tests | `tests/` (40 modules) | ✅ 217+ collectible; executor/policy/grants/HITL/sandbox/LLM/golden-eval covered |

Remaining hardening: Postgres-backed journal migration + pgvector retrieval,
policy-editor live-edit polish, multi-agent leaderboard/comparison polish,
decision-graph run-replay polish. See `STATUS.md` and `ROADMAP.md`.

---

## Quickstart

Full instructions: **`SETUP.md`**.

```powershell
git clone https://github.com/parth5012/warden
cd warden
Copy-Item .env.example .env   # then fill GROQ_API_KEY, WARDEN_APPROVER_KEYS, Clef (optional)
uv sync --extra dev
$env:PYTHONPATH='src'; uv run pytest -q        # kernel + available integration tests
$env:PYTHONPATH='src'; uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# → http://localhost:8000
```

Windows note: this repo's shell is PowerShell — use `$env:PYTHONPATH='src'`,
not `PYTHONPATH=src` or `export`.

---

## Repository map

```
├── README.md / SETUP.md          ← you are here / setup guide
├── ARCHITECTURE.md               ← system design (authoritative)
├── CONTEXT.md                    ← locked decisions + glossary
├── ROADMAP.md                    ← phases + exit criteria
├── STATUS.md                     ← what is built right now
├── DECISIONS.md                  ← decision log (post-lock changes)
├── .env.example                  ← copy to .env (Groq, approvers, Clef, sandbox)
├── pyproject.toml                ← uv project, strict mypy over src/tests/backend/frontend
├── src/warden/
│   ├── executor.py grants.py agent_engine.py config.py checkpoint.py demo_graph.py
│   ├── models.py journal.py wrappers.py
│   ├── policy/  hitl/  sandbox/  llm/  tools/  projections/
├── app/                          ← FastAPI console (dashboard, chat, grants, audit, …)
├── backend/api/                  ← JSON API (runs, inbox, audit, telemetry, policies, llm, auth, health)
├── frontend/                     ← Jinja views + static
├── tests/                        ← 40 modules incl. golden evals + Docker integration proofs
├── docs/                         ← index + contracts + features/ (14 slices)
└── scripts/                      ← demos (governed_demo, etc.)
```

---

## Verify

```powershell
$env:PYTHONPATH='src'
uv run pytest -q          # full suite (needs full deps for app/backend modules)
uv run mypy src tests     # strict typecheck
```

Collection baseline (2026-10-13): **217+ tests collectible**; 20 app/backend
modules need `psycopg` / `sqlglot` / `langgraph-checkpoint-postgres` from a
clean `uv sync --extra dev`.

---

## Documentation index

| Document | Purpose |
|---|---|
| `SETUP.md` | Environment setup, env vars, run + troubleshoot |
| `ARCHITECTURE.md` | Full system design, seam flow, data model, HTTP surface |
| `CONTEXT.md` | Locked decisions (1–12) + glossary — read before coding |
| `ROADMAP.md` | Phases 0–4 + exit criteria |
| `STATUS.md` | Build log — what exists vs. what is hardening |
| `DECISIONS.md` | Post-lock changes (Docker-only sandbox, layered policy, grants) |
| `docs/README.md` | Docs index + reading order |
| `docs/API_CONTRACT.md` | HTTP contracts |
| `docs/DATA_MODEL.md` | Domain types + persistence |
| `docs/LAYERED_SAFETY_ARCHITECTURE.md` | L0/L1/L2 policy detail |
| `docs/LOCAL_SETUP.md` | Quick-start reference (summary; `SETUP.md` is canonical) |
| `docs/features/` | Per-feature slices (all Phase-1 slices implemented) |

---

## Limitations (honest)

- **Postgres migration pending** — in-memory journal + SQLite approvals are
  live; full Postgres + pgvector migration is hardening work.
- **Docker required for sandbox proofs** — without a daemon the sandbox
  fail-closes to `Error(governance_unavailable)`; integration proofs skip
  cleanly via skip-gate.
- **Named-key auth is demo auth** — `name:key` pairs in env, recorded in the
  journal. Not real auth, doesn't pretend to be.
- **DENY is always terminal** — no approver or grant can override it. Fix the
  rule (versioned, audited), don't ask for an override.

---

## Contribution workflow

1. Read `CONTEXT.md` (locks) before writing code.
2. Check `STATUS.md` + the relevant `docs/features/` slice.
3. Use mock interfaces in `docs/INTEGRATION_GUIDE.md` only when a dependency
   is genuinely missing.
4. PRs must pass `uv run pytest` and `uv run mypy src tests`.
5. Never edit a lock in `CONTEXT.md` without a `DECISIONS.md` entry.

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: hackathon judges evaluating Warden live and in-repo. Situation: a timed demo plus code read-through (README → ARCHITECTURE → running FastAPI app). Job: grasp the governance story in minutes — one seam, four outcomes, human approval where policy is unsure — and verify it in the approvals inbox, blast-radius view, and audit trail.

## Product Purpose

Governance layer that LangGraph-based agents run *through*. Every action crosses a single, policy-enforced execution seam before it can touch the outside world: each call is journaled, checked against policy, sandboxed, and — when policy is unsure — parked for human approval before any side effect. Success for this surface: a judge can follow one escalated action from proposal → policy reason → blast-radius diff → approve/deny → audit evidence without explanation.

## Positioning

Single seam, no side channels: no agent node calls a tool or model directly; everything goes through `GuardedExecutor.execute(action, ctx) → Allowed | Denied | Pending | Error`. Both `tool` and `llm` kinds cross the same seam, so cost/latency telemetry and the decision graph are pure journal projections — never joined against callback logs.

## Operating Context

Phase 1 demo: one "ops assistant" graph (email + DB + shell tools) proving four bullets on one run — gate on send, deny on DROP TABLE, sandbox on rm -rf, cost/latency telemetry. App runs as one FastAPI process, server-rendered Jinja + HTMX, no build step. Local workflow: `uv sync`, `uv run pytest` (pgserver-backed), `uv run mypy src tests`.

## Capabilities and Constraints

- Outcomes: `Allowed(result)` / `Denied(reason, policy)` / `Pending(gate_request)` / `Error(reason)`; policy votes `allow | escalate | deny`, only `escalate` reaches a human.
- DENY is terminal — no human override; wrong rule means editing the versioned policy.
- Fail-closed: governance store unavailable → `Error(governance_unavailable)`, distinct from `Denied`; `execute()` never raises for environmental reasons.
- Write-ahead `action_requested` keyed `(run_id, action_id)` before any gate (idempotent node re-runs); checkpointer owns park/resume, journal owns what-happened; inbox reads the journal, never checkpoint state.
- Sandbox: every tool action via one port, Docker-contained; LLM actions skip sandbox (timeout + token accounting only).
- Approver identity = named `name:key` pairs, no login system; approvals must record a true `approver:` statement.
- Policies live in the DB (`policy_versions` append-only), seeded on first boot; pgvector beside the rows.
- UI constraint (locked): server-rendered in the FastAPI app, Jinja + HTMX, one process; endpoints stay JSON-clean for a future React lift. Undecided: nothing material open for this surface.

## Brand Commitments

Name = Warden (locked). Voice: technical, enforcement + oversight, plain-spoken about terminal DENY and fail-closed behavior. Existing assets to preserve: `app/templates/dashboard.html`, `approvals.html`, `blast_radius.html`, `base.html` + `app/static/`; demo dataset in `app/main.py` (`RAW_ACTIONS`, `RECENT_AUDIT_ACTIONS`, `ACTIVITY_BARS`). No invented brand palette or type system committed.

## Evidence on Hand

Real paths: `README.md`, `ARCHITECTURE.md`, `CONTEXT.md` (12 locked decisions), `ROADMAP.md`, `app/main.py`, `app/templates/dashboard.html`, `app/templates/approvals.html`, `app/templates/blast_radius.html`. Demo evidence: four proposed actions + five recent audit records + activity bars in `app/main.py`. Absences future work must not fabricate: no testimonials, customers, benchmarks, pricing, or production deployment claims.

## Product Principles

1. One seam over side channels — if it didn't cross `execute()`, it didn't happen.
2. Evidence before claims — the append-only journal is the story; views are projections.
3. Humans resolve only the unsure — escalate gets a gate, deny stays terminal.
4. Fail closed, never silent — infrastructure failure is an explicit Error outcome.
5. One graph must prove it all — gate, deny, sandbox, and telemetry on the single ops-assistant run.

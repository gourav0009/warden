# Aegis — Local Setup

> Exact prerequisites and commands to get Aegis running locally.
> For coding conventions and PR workflow, see [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md).

---

## Prerequisites

| Requirement | Version | How to install |
|---|---|---|
| Python | 3.11+ | https://python.org or `pyenv install 3.11` |
| uv | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Git | Any | https://git-scm.com |

> **PostgreSQL is not required separately.** The `pgserver` package bundles PostgreSQL 16 binaries. Tests and the CLI auto-start it.

---

## Step 1 — Clone and Install

```bash
git clone https://github.com/parth5012/warden
cd warden

# Install runtime + dev dependencies
uv sync --extra dev

# Verify
uv run python -c "import langgraph, psycopg, warden; print('Installation OK')"
```

---

## Step 2 — Run Tests

No additional setup needed. pgserver starts automatically.

```bash
$env:PYTHONPATH='src'; uv run pytest
```

Expected output: 200+ collected tests (40 modules). Some app/backend modules
require full deps (`psycopg`, `sqlglot`, `langgraph-checkpoint-postgres`) —
install with `uv sync --extra dev` from a clean venv; see SETUP.md.

---

## Step 3 — Type Check

```bash
$env:PYTHONPATH='src'; uv run mypy src tests
```

Strict mode over `src`, `tests`, `backend`, `frontend` (see `pyproject.toml`).

---

## Step 4 — Run the CLI Harness

```bash
uv run python tests/cli_chat.py
```

This auto-starts PostgreSQL (pgserver) and opens an interactive demo chat.

### CLI crash-recovery demo

```bash
# Terminal 1: start a run, park it, then Ctrl-C
uv run python tests/cli_chat.py
# you> hello
# *** GRAPH PARKED — human decision required ***
# resume> ^C   ← Ctrl-C here

# Terminal 2: restart and resume the same thread
uv run python tests/cli_chat.py --thread <thread-id-from-terminal-1>
# graph detects the parked state automatically
# resume> approve
# → Email sent
```

---

## Environment Variables (Optional)

```bash
# Override the PostgreSQL URI (default: bundled pgserver)
$env:WARDEN_PG_URI='postgresql://postgres:@/postgres?host=/tmp/warden-pg'

# Named approver keys (required for approval API)
$env:WARDEN_APPROVER_KEYS='alice:key-abc123,bob:key-def456'

# LLM provider (Groq default for governed chat; OpenAI/Anthropic optional)
$env:GROQ_API_KEY='gsk-...'
$env:GROQ_MODEL='openai/gpt-oss-20b'
$env:OPENAI_API_KEY='sk-...'

# Cloudflare Clef L2 (optional — FakeClefClient is used when unset, fail-closed on outage)
$env:CLOUDFLARE_ACCOUNT_ID='...'
$env:CLOUDFLARE_API_TOKEN='...'

# Sandbox container
$env:WARDEN_SANDBOX_WORKSPACE='D:/tmp'
$env:WARDEN_SANDBOX_IMAGE='python:3.11-slim'
```

Create a `.env` file for local development (it is in `.gitignore`):

```bash
# .env (not committed)
WARDEN_PG_URI=...
WARDEN_APPROVER_KEYS=alice:mykey
OPENAI_API_KEY=sk-...
```

---

## Starting the FastAPI App (implemented)

```bash
$env:PYTHONPATH='src'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The dashboard is at `http://localhost:8000` (live journal + telemetry +
pending gates + runs). JSON API under `/api/` (runs, inbox, audit,
telemetry, policies, llm, health). See `SETUP.md` for env vars
(`GROQ_API_KEY`, `WARDEN_APPROVER_KEYS`, Clef, sandbox).

---

## Troubleshooting

### pgserver fails to start

```bash
# Check pgserver is installed
uv run python -c "import pgserver; print('ok')"

# Try a fresh data directory
rm -rf /tmp/opencode/pgdata-warden
uv run python tests/cli_chat.py
```

### `uv sync` fails

```bash
# Verify Python version
python --version    # must be 3.11.x

# Clear uv cache and retry
uv cache clean
uv sync --extra dev
```

### mypy errors about `CompiledStateGraph`

Annotate as `CompiledStateGraph[Any, Any, Any, Any]`. See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md#11-troubleshooting).

### Tests fail with "connection refused"

pgserver may be starting slowly. Run `uv run pytest -v` to see more detail. If tests always fail on a fresh machine, check that the temp directory is writable.

### Import `from tests import cli_chat` fails

`tests/` must be a Python package. Verify `tests/__init__.py` exists. Do not add `mypy_path = ["tests"]` to `pyproject.toml`.

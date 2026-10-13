"""Aegis backend server: REST API plus the Aegis console pages from app/."""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

_ROOT_DIR = Path(__file__).resolve().parent.parent
_SRC_DIR = _ROOT_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from backend.api.health import router as health_router
from backend.api.inbox import router as inbox_router
from backend.api.runs import router as runs_router
from backend.api.audit import router as audit_router
from backend.api.telemetry import router as telemetry_router
from backend.api.policies import router as policies_router
from backend.api.auth import router as auth_router
from backend.api.llm import router as llm_router

from app.agents import router as agents_router
from app.audit import router as aegis_audit_router
from app.chat import router as chat_router
from app.grants import router as grants_router
from app.leases import router as leases_router
from app.llm import router as guarded_llm_router
from app.main import get_approvals, get_blast_radius
from app.policies import router as aegis_policies_router
from app.sandbox import router as sandbox_router
from app.traces import router as traces_router

_APP_STATIC_DIR = _ROOT_DIR / "app" / "static"


def create_app() -> FastAPI:
    """Create and configure the unified Aegis FastAPI application."""
    app = FastAPI(
        title="Aegis — AI Agent Governance",
        description="Unified server for AI agent governance, HITL approvals, telemetry, and audit logs.",
        version="0.1.0",
    )

    # Mount static assets from the Aegis console (app/)
    app.mount("/static", StaticFiles(directory=str(_APP_STATIC_DIR)), name="static")

    # Mount backend API routes under /api
    app.include_router(health_router, prefix="/api")
    app.include_router(inbox_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")
    app.include_router(audit_router, prefix="/api")
    app.include_router(telemetry_router, prefix="/api")
    app.include_router(policies_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(grants_router, prefix="/api")
    app.include_router(llm_router, prefix="/api")

    # Also mount health/ready at root per standard Kubernetes/container probes
    app.include_router(health_router)

    # Mount Aegis interactive chat and governance views (app/ console pages)
    app.include_router(chat_router)
    app.include_router(guarded_llm_router)
    app.include_router(grants_router)
    app.include_router(agents_router)
    app.include_router(leases_router)
    app.include_router(traces_router)
    app.include_router(sandbox_router)
    app.include_router(aegis_audit_router)
    app.include_router(aegis_policies_router)

    # Serve the Aegis shield icon so browsers never log a favicon 404.
    @app.get("/favicon.ico", include_in_schema=False)
    def favicon_page() -> FileResponse:
        return FileResponse(
            _APP_STATIC_DIR / "favicon.svg", media_type="image/svg+xml"
        )

    # The legacy standalone console was removed; send root visitors to the
    # interactive API docs instead of a bare 404.
    @app.get("/", include_in_schema=False)
    def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=307)

    # Mount Aegis action review endpoints
    @app.get("/approvals")
    def approvals_page(request: Request) -> Any:
        return get_approvals(request)

    @app.get("/actions/{action_id}")
    def blast_radius_page(request: Request, action_id: str) -> Any:
        return get_blast_radius(request, action_id)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

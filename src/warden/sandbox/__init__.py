"""Sandbox execution interfaces and adapters for Aegis.

Provides the SandboxPort boundary, execution result types, and the
backend factory. Docker is kept for local container isolation; subprocess
is the default (host-process, works where no Docker daemon exists).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from warden.sandbox.docker import DockerSandbox
from warden.sandbox.port import (
    SandboxPort,
    SandboxResult,
    SandboxUnavailable,
)
from warden.sandbox.registry import (
    ToolProfile,
    get_profile,
)
from warden.sandbox.subprocess import SubprocessSandbox

_DOCKER_BACKENDS = frozenset({"docker"})
_SUBPROCESS_BACKENDS = frozenset({"subprocess", "host", "local"})


def create_sandbox(
    workspace_path: Path | None = None,
    backend: str | None = None,
    registry_getter: Callable[[str], ToolProfile | None] = get_profile,
    image_override: str | None = None,
) -> SandboxPort:
    """Create the configured SandboxPort backend (fail-closed on unknown).

    Backend resolves from the explicit argument, else
    ``settings.sandbox_backend`` (``WARDEN_SANDBOX_BACKEND``), defaulting to
    ``subprocess``. Unknown backend names raise SandboxUnavailable, which the
    executor maps to Error(governance_unavailable) — never fall through to
    an unintended backend.
    """
    from warden.config import settings

    name = (backend or settings.sandbox_backend or "subprocess").strip().lower()
    workspace = workspace_path or settings.sandbox_workspace
    if name in _DOCKER_BACKENDS:
        return DockerSandbox(
            workspace_path=workspace,
            registry_getter=registry_getter,
            image_override=image_override or settings.sandbox_image or None,
        )
    if name in _SUBPROCESS_BACKENDS:
        return SubprocessSandbox(
            workspace_path=workspace,
            registry_getter=registry_getter,
        )
    raise SandboxUnavailable(f"Unknown sandbox backend: {backend or name!r}")


__all__ = [
    "DockerSandbox",
    "SandboxPort",
    "SandboxResult",
    "SandboxUnavailable",
    "SubprocessSandbox",
    "ToolProfile",
    "create_sandbox",
    "get_profile",
]

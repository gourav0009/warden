"""Subprocess sandbox adapter for tool execution in Aegis.

Host-process backend for environments without a container runtime (Render,
Railway, Fly). Runs exec-profile argv directly (never through a shell) with
the workspace as cwd, a scrubbed environment, a profile timeout, and a 64 KiB
output cap.

Best-effort containment only: cwd jail + timeout + secret scrubbing. There is
deliberately NO network-isolation claim here — that property belonged to the
Docker adapter (--network=none) and does not transfer. Unknown tool profiles
are refused (never run unprofiled); environmental failures are fail-closed
via SandboxUnavailable, which the executor maps to Error(governance_unavailable).
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from warden.models import Action, ActionKind
from warden.sandbox.port import (
    OUTPUT_CAP_BYTES,
    SandboxPort,
    SandboxResult,
    SandboxUnavailable,
)
from warden.sandbox.registry import ToolProfile, get_profile

TRUNCATION_MARKER = "...[truncated]"

# Parent env var NAMES matching this pattern are dropped before spawning the
# child. Deliberately name-based (not value-based): standard secret-bearing
# names (API keys, tokens, connection strings, approver keys) never cross.
SECRET_NAME_PATTERN = re.compile(
    r"secret|token|passwd|password|api[_-]?key|connection[_-]?string"
    r"|database[_-]?url|approver|private[_-]?key",
    re.IGNORECASE,
)


def _blocking_run(
    argv: list[str],
    timeout_s: float,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[bytes]:
    """Run a host process synchronously, capturing output.

    Executed inside ``asyncio.to_thread`` so sandboxed execution never depends
    on the running event loop's subprocess support. On Windows the process
    runs under ``WindowsSelectorEventLoopPolicy`` (forced by ``warden.config``
    for psycopg compatibility), where ``asyncio.create_subprocess_exec``
    raises ``NotImplementedError`` — this helper is immune to that.
    """
    return subprocess.run(
        argv, capture_output=True, timeout=timeout_s, cwd=str(cwd), env=env
    )


def _scrub_env() -> dict[str, str]:
    """Copy the parent environment minus secret-bearing variable names."""
    return {
        name: value
        for name, value in os.environ.items()
        if not SECRET_NAME_PATTERN.search(name)
    }


def _resolve_shell_argv(command: str) -> list[str]:
    """Resolve the host shell invocation for a shell-profile command.

    Prefers POSIX ``sh`` (Render/Linux, git-bash); falls back to ``cmd`` on
    Windows; fail-closed when neither exists.
    """
    sh = shutil.which("sh")
    if sh is not None:
        return [sh, "-c", command]
    if os.name == "nt":
        cmd = shutil.which("cmd")
        if cmd is not None:
            return [cmd, "/d", "/c", command]
    raise SandboxUnavailable(
        "No host shell binary available for shell-profile execution"
    )


def _truncate_output(raw_bytes: bytes) -> str:
    """Truncate output bytes exceeding OUTPUT_CAP_BYTES with trailing marker."""
    if len(raw_bytes) > OUTPUT_CAP_BYTES:
        truncated_bytes = raw_bytes[:OUTPUT_CAP_BYTES]
        return truncated_bytes.decode("utf-8", errors="replace") + TRUNCATION_MARKER
    return raw_bytes.decode("utf-8", errors="replace")


def _validate_payload(profile: ToolProfile, payload: Any) -> None:
    """Validate action payload structure against profile requirements."""
    if not isinstance(payload, dict):
        raise SandboxUnavailable("Action payload must be a dictionary")

    if profile.mode == "exec":
        argv = payload.get("argv")
        if not isinstance(argv, list) or len(argv) == 0:
            raise SandboxUnavailable(
                "Malformed payload for exec mode: 'argv' must be a non-empty list of strings"
            )
        for item in argv:
            if not isinstance(item, str) or not item.strip():
                raise SandboxUnavailable(
                    "Malformed payload for exec mode: each item in 'argv' must be a non-empty string"
                )
    elif profile.mode == "shell":
        command = payload.get("command")
        if not isinstance(command, str) or not command.strip():
            raise SandboxUnavailable(
                "Malformed payload for shell mode: 'command' must be a non-empty string"
            )
    else:
        raise SandboxUnavailable(f"Unsupported tool profile mode: {profile.mode}")


class SubprocessSandbox:
    """Host-subprocess sandbox implementing SandboxPort.

    Best-effort isolation: workspace cwd, scrubbed env, profile timeout,
    output cap. No container, no network namespace, no memory/CPU caps —
    callers must not claim otherwise.
    """

    def __init__(
        self,
        workspace_path: Path,
        registry_getter: Callable[[str], ToolProfile | None] = get_profile,
    ) -> None:
        self._workspace_path = workspace_path
        self._registry_getter = registry_getter

    async def run(self, action: Action) -> SandboxResult:
        """Execute a tool action as a host subprocess (asserts SandboxPort)."""
        if action.kind != ActionKind.TOOL:
            raise SandboxUnavailable(
                f"Unsupported action kind for sandbox: {action.kind}"
            )

        profile = self._registry_getter(action.name)
        if profile is None:
            raise SandboxUnavailable(f"Unknown tool profile: '{action.name}'")

        _validate_payload(profile, action.payload)

        try:
            workspace = self._workspace_path.resolve()
            workspace.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            raise SandboxUnavailable(
                f"Cannot prepare sandbox workspace: {err!r}"
            ) from err

        if profile.mode == "exec":
            argv: list[str] = list(action.payload["argv"])
        else:
            argv = _resolve_shell_argv(action.payload["command"])

        profile_tag = f"subprocess:{action.name}:{profile.mode}"
        start_time = time.monotonic()

        try:
            # to_thread: immune to Windows SelectorEventLoopPolicy, which
            # cannot spawn subprocesses via asyncio (see _blocking_run).
            completed = await asyncio.to_thread(
                _blocking_run,
                argv,
                float(profile.timeout_s),
                workspace,
                _scrub_env(),
            )
        except FileNotFoundError as err:
            raise SandboxUnavailable(
                f"Executable not found on PATH: {err!r}"
            ) from err
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return SandboxResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                timed_out=True,
                duration_ms=duration_ms,
                profile=profile_tag,
            )
        except asyncio.CancelledError:
            # No container to reconcile server-side; the worker thread runs
            # to completion and its output is discarded. Propagate.
            raise
        except Exception as err:
            raise SandboxUnavailable(
                f"Failed to run sandboxed subprocess: {err!r}"
            ) from err

        duration_ms = int((time.monotonic() - start_time) * 1000)
        stdout_text = _truncate_output(completed.stdout)
        stderr_text = _truncate_output(completed.stderr)
        returncode = completed.returncode

        return SandboxResult(
            ok=(returncode == 0),
            exit_code=returncode,
            stdout=stdout_text,
            stderr=stderr_text,
            timed_out=False,
            duration_ms=duration_ms,
            profile=profile_tag,
        )


def _assert_port_compliance() -> None:
    """Static check that SubprocessSandbox structurally satisfies SandboxPort."""
    _: SandboxPort = SubprocessSandbox(workspace_path=Path("/tmp"))


__all__ = ["SubprocessSandbox", "TRUNCATION_MARKER"]

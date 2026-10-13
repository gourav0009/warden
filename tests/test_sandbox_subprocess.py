"""Tests for SubprocessSandbox adapter (host-process backend for Render/hosting).

No Docker daemon required: exec mode runs argv directly (no shell), shell
mode runs via a host shell binary. Containment is best-effort (cwd jail +
timeout + scrubbed env) — there is deliberately NO network-isolation claim.

Validates:
1. Protocol compliance: SubprocessSandbox satisfies SandboxPort.
2. Unknown tool profile raises SandboxUnavailable (refuse, never run unprofiled).
3. Non-tool action kind raises SandboxUnavailable.
4. Malformed payload raises SandboxUnavailable:
   - exec mode: missing argv, empty argv, invalid argv types
   - shell mode: missing command, empty command, whitespace command
5. Real exec run: [sys.executable, "-c", "print(...)"] succeeds, cwd is workspace.
6. Real shell run: "echo hello" output captured.
7. Timeout returns SandboxResult(ok=False, exit_code=None, timed_out=True).
8. Truncation: stdout > OUTPUT_CAP_BYTES truncated with "...[truncated]" marker.
9. Missing executable raises SandboxUnavailable (fail-closed).
10. Profile field matches f"subprocess:{action.name}:{profile.mode}".
11. Secrets scrubbed from child env (e.g. GROQ_API_KEY must not leak through).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from warden.models import Action, ActionKind
from warden.sandbox import create_sandbox
from warden.sandbox.docker import DockerSandbox
from warden.sandbox.port import (
    OUTPUT_CAP_BYTES,
    SandboxPort,
    SandboxResult,
    SandboxUnavailable,
)
from warden.sandbox.registry import ToolProfile, get_profile
from warden.sandbox.subprocess import SubprocessSandbox


@pytest.fixture
def workspace_path(tmp_path: Path) -> Path:
    return tmp_path / "test_workspace"


def _exec_action(argv: list[Any], name: str = "file_inspect") -> Action:
    return Action(
        id="act-sub-01",
        kind=ActionKind.TOOL,
        name=name,
        payload={"argv": argv},
        run_id="run-sub-01",
        thread_id="thr-sub-01",
    )


def _shell_action(command: str) -> Action:
    return Action(
        id="act-sub-02",
        kind=ActionKind.TOOL,
        name="shell",
        payload={"command": command},
        run_id="run-sub-01",
        thread_id="thr-sub-01",
    )


def test_subprocess_sandbox_satisfies_sandbox_port_protocol(
    workspace_path: Path,
) -> None:
    """SubprocessSandbox must implement SandboxPort Protocol."""
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    assert isinstance(sandbox, SandboxPort)


def test_unknown_profile_raises_sandbox_unavailable(
    workspace_path: Path,
) -> None:
    """Unprofiled tools are refused, never executed."""

    async def _run() -> None:
        sandbox = SubprocessSandbox(workspace_path=workspace_path)
        action = Action(
            id="act-unknown",
            kind=ActionKind.TOOL,
            name="no-such-tool",
            payload={"argv": ["echo", "hi"]},
            run_id="r",
            thread_id="t",
        )
        await sandbox.run(action)

    import asyncio

    with pytest.raises(SandboxUnavailable, match="Unknown tool profile"):
        asyncio.run(_run())


def test_non_tool_kind_raises_sandbox_unavailable(
    workspace_path: Path,
) -> None:
    """LLM actions skip the sandbox (timeout + token accounting only)."""
    import asyncio

    async def _run() -> None:
        sandbox = SubprocessSandbox(workspace_path=workspace_path)
        action = Action(
            id="act-llm",
            kind=ActionKind.LLM,
            name="shell",
            payload={"command": "echo hi"},
            run_id="r",
            thread_id="t",
        )
        await sandbox.run(action)

    with pytest.raises(SandboxUnavailable, match="Unsupported action kind"):
        asyncio.run(_run())


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"argv": []},
        {"argv": ["", "  "]},
        {"argv": "echo hi"},
        {"argv": [123]},
    ],
)
def test_malformed_exec_payload_raises(
    workspace_path: Path, payload: dict[str, Any]
) -> None:
    """Exec mode requires a non-empty list of non-empty strings."""
    import asyncio

    async def _run() -> None:
        sandbox = SubprocessSandbox(workspace_path=workspace_path)
        await sandbox.run(_exec_action(payload.get("argv", payload)))

    with pytest.raises(SandboxUnavailable, match="Malformed payload"):
        asyncio.run(_run())


@pytest.mark.parametrize("command", ["", "   ", None, 123])
def test_malformed_shell_payload_raises(
    workspace_path: Path, command: Any
) -> None:
    """Shell mode requires a non-empty command string."""
    import asyncio

    async def _run() -> None:
        sandbox = SubprocessSandbox(workspace_path=workspace_path)
        action = Action(
            id="act-bad-shell",
            kind=ActionKind.TOOL,
            name="shell",
            payload={"command": command},
            run_id="r",
            thread_id="t",
        )
        await sandbox.run(action)

    with pytest.raises(SandboxUnavailable, match="Malformed payload"):
        asyncio.run(_run())


async def test_real_exec_run_captures_output(workspace_path: Path) -> None:
    """Real end-to-end exec run via the current Python interpreter."""
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    action = _exec_action([sys.executable, "-c", "print('hello-subprocess')"])
    result = await sandbox.run(action)
    assert isinstance(result, SandboxResult)
    assert result.ok is True
    assert result.exit_code == 0
    assert "hello-subprocess" in result.stdout
    assert result.timed_out is False
    assert result.profile == "subprocess:file_inspect:exec"


async def test_real_exec_runs_with_workspace_cwd(workspace_path: Path) -> None:
    """Child process cwd must be the configured workspace directory."""
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    action = _exec_action(
        [sys.executable, "-c", "import os; print(os.getcwd())"]
    )
    result = await sandbox.run(action)
    assert result.ok is True
    expected = str(workspace_path.resolve()).replace("\\", "/")
    assert expected in result.stdout.replace("\\", "/")


async def test_real_shell_run_captures_output(workspace_path: Path) -> None:
    """Shell mode executes the command string through a host shell."""
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    result = await sandbox.run(_shell_action("echo hello-shell"))
    assert result.ok is True
    assert "hello-shell" in result.stdout
    assert result.profile == "subprocess:shell:shell"


async def test_real_timeout_returns_timed_out(workspace_path: Path) -> None:
    """A run exceeding the profile timeout returns timed_out without raising."""
    profile = ToolProfile(
        name="slow_tool", mode="exec", mount="none", timeout_s=1
    )
    getter: Callable[[str], ToolProfile | None] = lambda name: (
        profile if name == "slow_tool" else None
    )
    sandbox = SubprocessSandbox(
        workspace_path=workspace_path, registry_getter=getter
    )
    action = _exec_action(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        name="slow_tool",
    )
    result = await sandbox.run(action)
    assert result.ok is False
    assert result.timed_out is True
    assert result.exit_code is None


async def test_truncation_caps_large_output(
    workspace_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stdout beyond OUTPUT_CAP_BYTES is truncated with a marker."""

    def fake_run(
        argv: list[str],
        timeout_s: float,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[bytes]:
        del argv, timeout_s, cwd, env
        return subprocess.CompletedProcess(
            args=["fake"],
            returncode=0,
            stdout=b"x" * (OUTPUT_CAP_BYTES + 100),
            stderr=b"",
        )

    monkeypatch.setattr(
        "warden.sandbox.subprocess._blocking_run", fake_run
    )
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    result = await sandbox.run(
        _exec_action([sys.executable, "-c", "print('x')"])
    )
    assert result.ok is True
    assert result.stdout.endswith("...[truncated]")
    assert len(result.stdout.encode("utf-8")) <= OUTPUT_CAP_BYTES + len(
        "...[truncated]"
    )


async def test_missing_executable_fail_closed(
    workspace_path: Path,
) -> None:
    """An argv binary that does not exist maps to SandboxUnavailable."""
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    with pytest.raises(SandboxUnavailable):
        await sandbox.run(
            _exec_action(["definitely-not-a-real-binary-xyz-123"])
        )


async def test_child_env_scrubs_secrets(
    workspace_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Secret-bearing parent env vars must not propagate to the child."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_secret_value")
    captured: dict[str, dict[str, str]] = {}

    real_run = subprocess.run

    def spy_run(*args: Any, **kwargs: Any) -> Any:
        captured["env"] = dict(kwargs.get("env") or {})
        return real_run(*args, **kwargs)

    monkeypatch.setattr(
        "warden.sandbox.subprocess.subprocess.run", spy_run
    )
    sandbox = SubprocessSandbox(workspace_path=workspace_path)
    result = await sandbox.run(
        _exec_action([sys.executable, "-c", "print('ok')"])
    )
    assert result.ok is True
    assert "GROQ_API_KEY" not in captured["env"]
    assert "gsk_test_secret_value" not in " ".join(captured["env"].values())


async def test_registry_seed_profiles_unchanged() -> None:
    """The swap must not alter the tool-profile registry contract."""
    assert get_profile("shell") is not None
    assert get_profile("file_inspect") is not None
    assert get_profile("no-such-tool") is None


def test_factory_defaults_to_subprocess(
    workspace_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unset backend -> host-process backend (Render-safe default)."""
    from warden import config

    monkeypatch.setattr(config.settings, "sandbox_backend", "subprocess")
    sandbox = create_sandbox(workspace_path=workspace_path)
    assert isinstance(sandbox, SubprocessSandbox)


def test_factory_selects_backends_explicitly(
    workspace_path: Path,
) -> None:
    """Explicit backend names resolve to the matching adapter."""
    assert isinstance(
        create_sandbox(workspace_path=workspace_path, backend="subprocess"),
        SubprocessSandbox,
    )
    assert isinstance(
        create_sandbox(workspace_path=workspace_path, backend="docker"),
        DockerSandbox,
    )


def test_factory_unknown_backend_fail_closed(
    workspace_path: Path,
) -> None:
    """Unknown backend names raise instead of falling through elsewhere."""
    with pytest.raises(SandboxUnavailable, match="Unknown sandbox backend"):
        create_sandbox(workspace_path=workspace_path, backend="bogus")

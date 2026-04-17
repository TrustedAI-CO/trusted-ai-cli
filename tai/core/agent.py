"""Core logic for spawning AI coding agents (Codex / Gemini CLI) as subprocesses."""

from __future__ import annotations

import asyncio
import shutil
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class AgentBackend(str, Enum):
    CODEX = "codex"
    GEMINI = "gemini"


class AgentStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class AgentTask:
    id: str
    prompt: str
    backend: AgentBackend
    working_dir: str | None = None
    model: str | None = None
    timeout: float = 300.0
    sandbox: bool = False


@dataclass(frozen=True)
class AgentResult:
    id: str
    backend: AgentBackend
    status: AgentStatus
    output: str
    duration_s: float
    exit_code: int | None


def create_task(
    prompt: str,
    *,
    backend: AgentBackend = AgentBackend.CODEX,
    working_dir: str | None = None,
    model: str | None = None,
    timeout: float = 300.0,
    sandbox: bool = False,
) -> AgentTask:
    return AgentTask(
        id=uuid.uuid4().hex[:8],
        prompt=prompt,
        backend=backend,
        working_dir=working_dir,
        model=model,
        timeout=timeout,
        sandbox=sandbox,
    )


def _check_binary(backend: AgentBackend) -> None:
    """Raise if the backend CLI is not installed."""
    if shutil.which(backend.value) is None:
        hints = {
            AgentBackend.CODEX: "npm install -g @openai/codex",
            AgentBackend.GEMINI: "npm install -g @google/gemini-cli",
        }
        raise FileNotFoundError(
            f"'{backend.value}' not found in PATH. Install: {hints[backend]}"
        )


def _build_codex_args(task: AgentTask) -> list[str]:
    args = ["exec", "--full-auto", "--json", "--skip-git-repo-check"]
    if task.working_dir:
        args.extend(["--cd", task.working_dir])
    if task.model:
        args.extend(["--model", task.model])
    args.append(task.prompt)
    return args


def _build_gemini_args(task: AgentTask) -> list[str]:
    args = ["--prompt", task.prompt, "--output-format", "json", "--yolo"]
    if task.model:
        args.extend(["--model", task.model])
    if task.sandbox:
        args.append("--sandbox")
    return args


async def _run_one(task: AgentTask) -> AgentResult:
    """Run a single agent task as an async subprocess."""
    _check_binary(task.backend)

    command = task.backend.value
    args = (
        _build_codex_args(task)
        if task.backend == AgentBackend.CODEX
        else _build_gemini_args(task)
    )
    cwd = task.working_dir if task.backend == AgentBackend.GEMINI else None

    loop = asyncio.get_event_loop()
    start = loop.time()

    proc = await asyncio.create_subprocess_exec(
        command,
        *args,
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    timed_out = False
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=task.timeout
        )
    except asyncio.TimeoutError:
        timed_out = True
        proc.terminate()
        stdout, stderr = await proc.communicate()

    duration = loop.time() - start
    output = (stdout or b"").decode() + (stderr or b"").decode()

    if timed_out:
        status = AgentStatus.TIMEOUT
    elif proc.returncode == 0:
        status = AgentStatus.SUCCESS
    else:
        status = AgentStatus.ERROR

    return AgentResult(
        id=task.id,
        backend=task.backend,
        status=status,
        output=output.strip(),
        duration_s=round(duration, 2),
        exit_code=proc.returncode,
    )


def run_agent(task: AgentTask) -> AgentResult:
    """Run a single agent task synchronously."""
    return asyncio.run(_run_one(task))


def run_parallel(tasks: Sequence[AgentTask], max_concurrent: int = 5) -> list[AgentResult]:
    """Run multiple agent tasks concurrently."""

    async def _gather() -> list[AgentResult]:
        sem = asyncio.Semaphore(max_concurrent)

        async def _limited(t: AgentTask) -> AgentResult:
            async with sem:
                return await _run_one(t)

        return list(await asyncio.gather(*(_limited(t) for t in tasks)))

    return asyncio.run(_gather())

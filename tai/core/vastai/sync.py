"""Transfer the user's repos onto the remote box.

Strategy per repo path:

1. **Clone the tracked tree** on the server using ``git clone`` over the
   forwarded SSH agent. The repo is cloned at ``<remote_root>/<basename>``.
   If it isn't a git repo we skip the clone and rsync the whole tree.

2. **rsync uncommitted work** — modified-but-tracked + untracked-non-ignored
   files only. This carries WIP without dragging in ``.venv``,
   ``node_modules``, etc.

3. **rsync explicit ignored includes** (one rsync per path) for things like
   ``data/`` or ``.env`` that the user opted into via ``--include-ignored``.

The functions here are pure builders — they return command lists so tests
can assert against them without invoking rsync/git.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from tai.core.errors import TaiError

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]

HARD_BLOCK_PATTERNS: tuple[str, ...] = (
    ".git/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "node_modules/",
    "target/",
    "dist/",
    "build/",
    ".DS_Store",
    "*.pyc",
)

# Patterns that are valid to include with --include-ignored but should
# trigger a "you sure?" warning at the CLI layer.
SECRET_WARN_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "credentials.json",
)


@dataclass(frozen=True)
class RemoteTarget:
    ssh_alias: str           # the Host alias from ~/.ssh/config (e.g. vastai-quick-gpu)
    remote_root: str = "/root"


def _default_runner(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _git(repo: Path, args: Sequence[str], runner: Runner) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git") or "git"
    return runner([git, "-C", str(repo), *args])


def is_git_repo(repo: Path, runner: Runner | None = None) -> bool:
    runner = runner or _default_runner
    result = _git(repo, ["rev-parse", "--is-inside-work-tree"], runner)
    return result.returncode == 0 and result.stdout.strip() == "true"


def remote_origin_url(repo: Path, runner: Runner | None = None) -> str | None:
    runner = runner or _default_runner
    result = _git(repo, ["remote", "get-url", "origin"], runner)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def uncommitted_files(repo: Path, runner: Runner | None = None) -> list[str]:
    """Modified tracked + untracked-non-ignored, repo-relative."""
    runner = runner or _default_runner
    modified = _git(repo, ["diff", "--name-only", "-z", "HEAD"], runner)
    untracked = _git(repo, ["ls-files", "--others", "--exclude-standard", "-z"], runner)
    files: list[str] = []
    for blob in (modified.stdout, untracked.stdout):
        for entry in blob.split("\0"):
            entry = entry.strip()
            if entry and entry not in files:
                files.append(entry)
    return files


def build_clone_cmd(
    *,
    target: RemoteTarget,
    origin_url: str,
    branch: str | None,
    repo_basename: str,
) -> list[str]:
    """Run via ssh: clone origin into remote_root/repo_basename."""
    ssh = shutil.which("ssh") or "ssh"
    remote_path = f"{target.remote_root.rstrip('/')}/{repo_basename}"
    # -A forwards the agent so the remote `git` can auth as the user.
    git_cmd = (
        f"set -e; mkdir -p {target.remote_root}; "
        f"if [ -d {remote_path}/.git ]; then "
        f"  cd {remote_path} && git fetch --all --prune; "
        f"else "
        f"  git clone {origin_url} {remote_path}"
        + (f" --branch {branch}" if branch else "")
        + "; fi"
    )
    return [ssh, "-A", target.ssh_alias, git_cmd]


def build_rsync_cmd(
    *,
    target: RemoteTarget,
    local_root: Path,
    files: Iterable[str],
    repo_basename: str,
) -> list[str] | None:
    """rsync a small explicit file list. Returns None if files is empty."""
    files = list(files)
    if not files:
        return None
    rsync = shutil.which("rsync") or "rsync"
    remote_path = f"{target.remote_root.rstrip('/')}/{repo_basename}/"
    return [
        rsync,
        "-az",
        "--relative",
        "--files-from=-",
        str(local_root) + "/",
        f"{target.ssh_alias}:{remote_path}",
    ]


def build_rsync_ignored_cmd(
    *,
    target: RemoteTarget,
    local_root: Path,
    include_path: str,
    repo_basename: str,
) -> list[str]:
    """rsync a single user-specified ignored path (e.g. data/, .env)."""
    rsync = shutil.which("rsync") or "rsync"
    src = (local_root / include_path).resolve()
    if not src.exists():
        raise TaiError(
            f"Ignored include path does not exist: {src}",
            hint=f"Check the path; it must be relative to {local_root} or absolute.",
        )
    excludes: list[str] = []
    for pat in HARD_BLOCK_PATTERNS:
        excludes.extend(["--exclude", pat])
    remote_path = f"{target.remote_root.rstrip('/')}/{repo_basename}/{include_path.lstrip('/')}"
    if src.is_dir() and not str(src).endswith("/"):
        src_arg = str(src) + "/"
    else:
        src_arg = str(src)
    return [
        rsync,
        "-az",
        *excludes,
        src_arg,
        f"{target.ssh_alias}:{remote_path}",
    ]


def is_secret_path(path: str) -> bool:
    """True if `path` matches a SECRET_WARN_PATTERNS entry by basename."""
    from fnmatch import fnmatch
    base = Path(path).name
    return any(fnmatch(base, pat) for pat in SECRET_WARN_PATTERNS)

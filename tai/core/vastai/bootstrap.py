"""Build the remote install script and the credential-copy plan.

The remote-install script is rendered as a single bash blob so we can
pipe it over ``ssh <alias> bash -s`` and get one round-trip. Tests
inspect the rendered text rather than executing it.

trusted-ai-cli is not on PyPI today, so the install script accepts an
optional remote wheel path (uploaded by the up flow before invocation).
When provided, ``uv tool install`` installs from that path; otherwise it
falls back to PyPI (will fail until the package is published).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_INSTALL_SCRIPT_TEMPLATE = r"""#!/usr/bin/env bash
set -euo pipefail

echo "[tai] seeding ~/.ssh/known_hosts with common git hosts..."
mkdir -p ~/.ssh && chmod 700 ~/.ssh
touch ~/.ssh/known_hosts && chmod 644 ~/.ssh/known_hosts
for host in github.com gitlab.com bitbucket.org ssh.dev.azure.com; do
    ssh-keygen -F "$host" >/dev/null 2>&1 || \
        ssh-keyscan -t rsa,ecdsa,ed25519 "$host" >> ~/.ssh/known_hosts 2>/dev/null || true
done

echo "[tai] installing uv..."
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "[tai] installing trusted-ai-cli..."
{install_line}

echo "[tai] ensuring node >= 20 (claude-code + codex require >= 18)..."
node_major=0
if command -v node >/dev/null 2>&1; then
    node_major=$(node -v | sed -E 's/^v([0-9]+)\..*/\1/')
fi
if [ "${{node_major:-0}}" -lt 18 ]; then
    # NodeSource's nodejs package conflicts with Ubuntu's libnode-dev/libnode72.
    apt-get remove -y libnode-dev libnode72 nodejs-doc 2>/dev/null || true
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - || true
    apt-get install -y nodejs || true
fi

echo "[tai] installing claude code + codex..."
if command -v npm >/dev/null 2>&1; then
    npm install -g @anthropic-ai/claude-code @openai/codex || true
fi

echo "[tai] installing tai skills for claude code + codex..."
"$HOME/.local/bin/tai" claude setup-skills --force || tai claude setup-skills --force || true
"$HOME/.local/bin/tai" codex  setup-skills --force || tai codex  setup-skills --force || true

echo "[tai] bootstrap done."
"""


def render_install_script(wheel_remote_path: str | None = None) -> str:
    """Render the remote install script. If a remote wheel path is given,
    install from that file; otherwise install from PyPI (currently fails)."""
    if wheel_remote_path:
        # Use uv (no fallback to pip — pip can't always install local wheels for tools).
        install_line = f'uv tool install --force "{wheel_remote_path}"'
    else:
        install_line = (
            "uv tool install --force trusted-ai-cli "
            "|| pip install --user --upgrade trusted-ai-cli"
        )
    return _INSTALL_SCRIPT_TEMPLATE.format(install_line=install_line)


# Back-compat: many call sites used REMOTE_INSTALL_SCRIPT directly. Keep as
# the no-wheel rendering so they continue to work.
REMOTE_INSTALL_SCRIPT = render_install_script(None)


# Files we will rsync from the user's machine to the remote, keyed by
# local path → remote path. Anything missing locally is silently skipped.
AGENT_CRED_PATHS: dict[str, str] = {
    "~/.claude/.credentials.json": "~/.claude/.credentials.json",
    "~/.codex/auth.json": "~/.codex/auth.json",
}


@dataclass(frozen=True)
class CredCopyPlan:
    """A planned credential file copy."""

    local: Path
    remote: str  # remote path (may contain ~)
    is_secret: bool = True


def plan_cred_copy(
    *,
    enabled: bool,
    home: Path | None = None,
    paths: dict[str, str] | None = None,
) -> list[CredCopyPlan]:
    """Resolve which AGENT_CRED_PATHS exist locally and should be copied."""
    if not enabled:
        return []
    home = home or Path.home()
    paths = paths or AGENT_CRED_PATHS
    plans: list[CredCopyPlan] = []
    for local_pat, remote in paths.items():
        local = Path(local_pat.replace("~", str(home))).expanduser()
        if local.is_file():
            plans.append(CredCopyPlan(local=local, remote=remote))
    return plans


def build_install_command(ssh_alias: str) -> list[str]:
    """Pipe the install script over ssh: `ssh alias bash -s` < script."""
    import shutil
    ssh = shutil.which("ssh") or "ssh"
    return [ssh, ssh_alias, "bash", "-s"]


def find_tai_source_root(start: Path | None = None) -> Path | None:
    """Walk up from `start` (or cwd) for a pyproject.toml that names this package.

    Returns the directory or None if not found.
    """
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        pyproject = candidate / "pyproject.toml"
        if pyproject.is_file():
            try:
                text = pyproject.read_text()
            except OSError:
                continue
            if 'name = "trusted-ai-cli"' in text or "name = 'trusted-ai-cli'" in text:
                return candidate
    return None


def build_wheel(source_root: Path, out_dir: Path) -> Path:
    """Build a wheel from a source tree using `uv build --wheel`.

    Returns the path to the freshly built wheel. Raises if no wheel is found.
    """
    import shutil
    import subprocess
    uv = shutil.which("uv") or "uv"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Wipe any stale wheels so the glob below picks the new one.
    for existing in out_dir.glob("*.whl"):
        existing.unlink()
    result = subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(out_dir)],
        cwd=str(source_root),
        capture_output=True,
        text=True,
        check=False,
    )
    wheels = list(out_dir.glob("*.whl"))
    if result.returncode != 0 or not wheels:
        raise RuntimeError(
            f"uv build failed (rc={result.returncode}): "
            f"{(result.stderr or result.stdout).strip()}"
        )
    return wheels[0]


def build_wheel_upload_commands(
    *, ssh_alias: str, wheel_path: Path, remote_dir: str = "/tmp",
) -> tuple[list[list[str]], str]:
    """Commands to ensure remote_dir exists and scp the wheel into it.

    Returns (commands, remote_wheel_path) — pass remote_wheel_path into
    :func:`render_install_script`.
    """
    import shutil
    ssh = shutil.which("ssh") or "ssh"
    scp = shutil.which("scp") or "scp"
    remote = f"{remote_dir.rstrip('/')}/{wheel_path.name}"
    cmds = [
        [ssh, ssh_alias, "mkdir", "-p", remote_dir],
        [scp, str(wheel_path), f"{ssh_alias}:{remote}"],
    ]
    return cmds, remote


def build_cred_copy_commands(
    *,
    ssh_alias: str,
    plans: list[CredCopyPlan],
) -> list[list[str]]:
    """Two-step per cred: ensure remote dir, scp the file, chmod 600."""
    import shutil
    ssh = shutil.which("ssh") or "ssh"
    scp = shutil.which("scp") or "scp"
    cmds: list[list[str]] = []
    for plan in plans:
        remote_dir = plan.remote.rsplit("/", 1)[0] or "/"
        cmds.append([ssh, ssh_alias, "mkdir", "-p", remote_dir])
        cmds.append([scp, str(plan.local), f"{ssh_alias}:{plan.remote}"])
        cmds.append([ssh, ssh_alias, "chmod", "600", plan.remote])
    return cmds


def build_remote_shred_command(
    *,
    ssh_alias: str,
    remote_paths: list[str],
    connect_timeout_s: int = 10,
) -> list[str]:
    """Best-effort wipe of secrets + repo trees on the remote box.

    Uses a short ConnectTimeout so an unreachable box fails fast (the
    container is about to be destroyed anyway). Caller should treat
    failures as warnings, not hard errors.
    """
    import shlex
    import shutil
    ssh = shutil.which("ssh") or "ssh"
    # Repo paths come from the saved state — quote them in case a
    # basename has shell metachars. Well-known patterns (~, glob) need
    # shell expansion so we write them inline rather than quoting.
    quoted_repos = " ".join(shlex.quote(p) for p in remote_paths)
    # `set +e` + explicit `exit 0`: any single rm failing must not stop
    # the rest from running, and we want rc=0 so the destroy step still
    # fires even if shred had problems.
    script = (
        "set +e; "
        'rm -rf "$HOME/.claude" "$HOME/.codex"; '
        "rm -f /tmp/trusted_ai_cli-*.whl; "
        f"rm -rf {quoted_repos}; "
        "exit 0"
    )
    return [
        ssh,
        "-o", f"ConnectTimeout={connect_timeout_s}",
        "-o", "BatchMode=yes",
        ssh_alias,
        "bash", "-c", script,
    ]


def shred_paths_for_state(
    *, repo_paths: list[str], remote_repo_root: str,
) -> list[str]:
    """Map local repo paths in the saved state to their remote counterparts."""
    from pathlib import PurePosixPath
    root = remote_repo_root.rstrip("/") or "/"
    return [str(PurePosixPath(root) / Path(p).name) for p in repo_paths]

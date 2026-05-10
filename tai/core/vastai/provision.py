"""Create an instance, attach an SSH key, wait until SSH is reachable.

This module is structured around a single :class:`Provisioner` so tests
can swap out its `runner` (subprocess hook) and `sleeper` (time.sleep
hook) without monkeypatching globals.
"""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from tai.core.errors import TaiError
from tai.core.vastai.offers import _ensure_vastai

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
Sleeper = Callable[[float], None]


@dataclass
class CreatedInstance:
    instance_id: int
    ssh_host: str
    ssh_port: int
    ssh_user: str = "root"


def _default_runner(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def ssh_key_path_for(alias: str, base: Path | None = None) -> Path:
    base = base or (Path.home() / ".ssh")
    return base / f"vastai_{alias}_ed25519"


def generate_ssh_key(alias: str, *, base: Path | None = None, runner: Runner | None = None) -> Path:
    """Create a dedicated ed25519 keypair for this alias if missing."""
    runner = runner or _default_runner
    key_path = ssh_key_path_for(alias, base=base)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return key_path
    keygen = shutil.which("ssh-keygen") or "ssh-keygen"
    result = runner([
        keygen, "-t", "ed25519", "-N", "", "-f", str(key_path),
        "-C", f"tai-vastai-{alias}",
    ])
    if result.returncode != 0 or not key_path.exists():
        raise TaiError(
            "ssh-keygen failed",
            hint=(result.stderr or result.stdout or "").strip(),
        )
    try:
        key_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return key_path


class Provisioner:
    def __init__(
        self,
        *,
        runner: Runner | None = None,
        sleeper: Sleeper | None = None,
        poll_interval_s: float = 5.0,
        max_wait_s: float = 600.0,
    ):
        self.runner = runner or _default_runner
        self.sleeper = sleeper or time.sleep
        self.poll_interval_s = poll_interval_s
        self.max_wait_s = max_wait_s
        self._binary: str | None = None

    def _vastai(self) -> str:
        binary = self._binary
        if binary is None:
            binary = _ensure_vastai()
            self._binary = binary
        return binary

    def _run_vastai_json(self, args: Sequence[str]) -> dict | list:
        cmd = [self._vastai(), *args, "--raw"]
        result = self.runner(cmd)
        if result.returncode != 0:
            raise TaiError(
                f"vastai {' '.join(args)} failed",
                hint=(result.stderr or result.stdout or "").strip(),
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise TaiError("Could not parse vastai response", hint=result.stdout[:200]) from exc

    def create_instance(
        self,
        *,
        offer_id: int,
        image: str,
        disk_gb: int,
        alias: str,
        onstart_cmd: str | None = None,
    ) -> int:
        args = [
            "create", "instance", str(offer_id),
            "--image", image,
            "--disk", str(disk_gb),
            "--ssh", "--direct",
            "--label", f"tai-vastai-{alias}",
        ]
        if onstart_cmd:
            args.extend(["--onstart-cmd", onstart_cmd])
        payload = self._run_vastai_json(args)
        if not isinstance(payload, dict) or not payload.get("success", False):
            raise TaiError(
                "vastai did not confirm instance creation",
                hint=str(payload),
            )
        new_id = payload.get("new_contract") or payload.get("instance_id")
        if not new_id:
            raise TaiError("vastai response missing new_contract id", hint=str(payload))
        return int(new_id)

    def attach_ssh_key(self, instance_id: int, public_key: str) -> None:
        cmd = [self._vastai(), "attach", "ssh", str(instance_id), public_key.strip()]
        result = self.runner(cmd)
        if result.returncode != 0:
            raise TaiError(
                "vastai attach ssh failed",
                hint=(result.stderr or result.stdout or "").strip(),
            )

    def wait_for_ssh(self, instance_id: int) -> CreatedInstance:
        """Poll `vastai show instance` until ssh_host/ssh_port appear."""
        deadline = time.monotonic() + self.max_wait_s
        last_status = ""
        while time.monotonic() < deadline:
            data = self._run_vastai_json(["show", "instance", str(instance_id)])
            if isinstance(data, list):
                data = data[0] if data else {}
            assert isinstance(data, dict)
            status = data.get("actual_status") or data.get("status_msg") or ""
            last_status = status
            host = data.get("ssh_host")
            port = data.get("ssh_port")
            if status == "running" and host and port:
                return CreatedInstance(
                    instance_id=instance_id,
                    ssh_host=str(host),
                    ssh_port=int(port),
                )
            self.sleeper(self.poll_interval_s)
        raise TaiError(
            f"Instance {instance_id} did not become reachable within {int(self.max_wait_s)}s",
            hint=f"Last status: {last_status or 'unknown'}. Inspect with `vastai show instance {instance_id}`.",
        )

    def smoke_test_ssh(self, instance: CreatedInstance, ssh_key_path: Path) -> None:
        ssh = shutil.which("ssh") or "ssh"
        cmd = [
            ssh,
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=15",
            "-i", str(ssh_key_path),
            "-p", str(instance.ssh_port),
            f"{instance.ssh_user}@{instance.ssh_host}",
            "echo ok",
        ]
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            result = self.runner(cmd)
            if result.returncode == 0 and "ok" in result.stdout:
                return
            self.sleeper(5)
        raise TaiError(
            "Could not establish SSH to the new instance",
            hint=f"Try manually: ssh -i {ssh_key_path} -p {instance.ssh_port} {instance.ssh_user}@{instance.ssh_host}",
        )

    def destroy_instance(self, instance_id: int) -> None:
        # `-y` is required: without it vastai prompts on stdin, then aborts
        # and exits 0 — a silent no-op masquerading as success.
        cmd = [self._vastai(), "destroy", "instance", str(instance_id), "-y"]
        result = self.runner(cmd)
        if result.returncode != 0:
            raise TaiError(
                f"vastai destroy instance {instance_id} failed",
                hint=(result.stderr or result.stdout or "").strip(),
            )

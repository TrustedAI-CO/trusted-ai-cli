"""tai vastai — quick-GPU provisioning on vast.ai.

Subcommands:

    tai vastai up      provision a cheapest-match instance + sync repos
    tai vastai down    destroy an instance and clean up local config
    tai vastai list    show recorded aliases and their instance ids
    tai vastai status  inspect a single alias

The skill ``vastai-quick-gpu`` is the agent-facing entry point and shells
out to these commands. Logic lives in :mod:`tai.core.vastai.*` so it's
testable without spending money on real GPUs.
"""

from __future__ import annotations

import json as jsonlib
import shlex
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import TaiError
from tai.core.vastai import bootstrap as bootstrap_mod
from tai.core.vastai import offers as offers_mod
from tai.core.vastai import provision as provision_mod
from tai.core.vastai import ssh_config as ssh_config_mod
from tai.core.vastai import state as state_mod
from tai.core.vastai import sync as sync_mod

app = typer.Typer(name="vastai", help="Quick-GPU provisioning on vast.ai.")
console = Console()
err_console = Console(stderr=True)


def _emit(payload: dict, *, json_output: bool, success_message: str | None = None) -> None:
    if json_output:
        console.print_json(jsonlib.dumps(payload))
    elif success_message:
        console.print(success_message)


def _confirm(prompt: str, *, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    try:
        return typer.confirm(prompt, default=False)
    except typer.Abort:
        return False


def _run_or_raise(cmd: list[str], *, stdin: str | None = None) -> str:
    result = subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise TaiError(
            f"Command failed: {' '.join(shlex.quote(c) for c in cmd)}",
            hint=(result.stderr or result.stdout or "").strip(),
        )
    return result.stdout


@app.command("up")
def up(
    gpu: str = typer.Option(..., "--gpu", help="GPU model (e.g. RTX_5090, H100)."),
    disk: int = typer.Option(100, "--disk", help="Disk size in GB."),
    region: str = typer.Option("any", "--region", help="any | us | na | eu | asia | comma-separated country codes."),
    alias: str = typer.Option("quick-gpu", "--alias", help="Local alias for this instance."),
    repo: list[Path] = typer.Option([], "--repo", help="Repo path(s) to sync. Repeatable."),
    include_ignored: list[str] = typer.Option(
        [], "--include-ignored",
        help="Path inside the repo to also sync, even if gitignored (e.g. data, .env). Repeatable.",
    ),
    image: str = typer.Option(
        "pytorch/pytorch:latest",
        "--image",
        help="Docker image to launch.",
    ),
    copy_agent_creds: bool = typer.Option(
        True, "--copy-agent-creds/--no-copy-agent-creds",
        help="Copy ~/.claude and ~/.codex auth files to the new box.",
    ),
    tai_source: Optional[Path] = typer.Option(
        None, "--tai-source",
        help="Path to a local trusted-ai-cli source tree. If set, build a wheel "
             "from there and ship it to the box (for testing uncommitted "
             "changes). Default: install latest main from git+https.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip price confirmation."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Search, create, and configure a cheapest-match GPU instance."""
    try:
        chosen_alias = state_mod.next_available_alias(alias)
        query = offers_mod.OfferQuery(gpu=gpu, disk_gb=disk, region=region)
        offers_list = offers_mod.search_offers(query)
        offer = offers_mod.pick_cheapest(offers_list)
        summary = offers_mod.summarise_offer(offer)

        if not yes:
            console.print(
                f"[bold]Cheapest match[/bold]: {summary['gpu_name']} x{summary['num_gpus']}"
                f" — ${summary['dph_total']:.4f}/hr — {summary['geolocation']}"
                f" — disk {summary['disk_space_gb']} GB — reliability {summary['reliability']}"
            )
            if not _confirm(f"Provision instance {summary['id']} as alias {chosen_alias!r}?", assume_yes=False):
                raise TaiError("Aborted by user.", hint="Re-run with --yes to skip confirmation.")

        provisioner = provision_mod.Provisioner()
        ssh_key = provision_mod.generate_ssh_key(chosen_alias)
        pub_key = (Path(str(ssh_key) + ".pub")).read_text().strip()

        instance_id = provisioner.create_instance(
            offer_id=int(summary["id"]),
            image=image,
            disk_gb=disk,
            alias=chosen_alias,
        )
        provisioner.attach_ssh_key(instance_id, pub_key)
        instance = provisioner.wait_for_ssh(instance_id)

        block = ssh_config_mod.render_block(
            alias=chosen_alias,
            hostname=instance.ssh_host,
            port=instance.ssh_port,
            user=instance.ssh_user,
            identity_file=str(ssh_key),
        )
        ssh_config_mod.upsert_block(block, alias=chosen_alias)

        provisioner.smoke_test_ssh(instance, ssh_key)

        host_alias = ssh_config_mod.host_alias(chosen_alias)

        if copy_agent_creds:
            plans = bootstrap_mod.plan_cred_copy(enabled=True)
            for cmd in bootstrap_mod.build_cred_copy_commands(ssh_alias=host_alias, plans=plans):
                _run_or_raise(cmd)

        # By default the remote installs trusted-ai-cli from git+https
        # (the repo is public, no auth needed). Pass --tai-source to ship a
        # local wheel instead — useful for testing uncommitted changes.
        remote_wheel: str | None = None
        if tai_source is not None and str(tai_source).strip():
            source_root = Path(str(tai_source).strip()).expanduser().resolve()
            if not (source_root / "pyproject.toml").is_file():
                raise TaiError(
                    f"--tai-source path has no pyproject.toml: {source_root}",
                )
            import tempfile
            wheel_dir = Path(tempfile.mkdtemp(prefix="tai-wheel-"))
            wheel = bootstrap_mod.build_wheel(source_root, wheel_dir)
            upload_cmds, remote_wheel = bootstrap_mod.build_wheel_upload_commands(
                ssh_alias=host_alias, wheel_path=wheel,
            )
            for cmd in upload_cmds:
                _run_or_raise(cmd)

        _run_or_raise(
            bootstrap_mod.build_install_command(host_alias),
            stdin=bootstrap_mod.render_install_script(remote_wheel),
        )

        synced_repos: list[dict] = []
        target = sync_mod.RemoteTarget(ssh_alias=host_alias)
        for repo_path in repo:
            repo_path = repo_path.expanduser().resolve()
            if not repo_path.is_dir():
                raise TaiError(f"Repo path not found: {repo_path}")
            basename = repo_path.name
            entry: dict = {"local": str(repo_path), "remote": f"{target.remote_root}/{basename}"}
            if sync_mod.is_git_repo(repo_path):
                origin = sync_mod.remote_origin_url(repo_path)
                if origin:
                    branch = _run_or_raise(["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"]).strip()
                    _run_or_raise(sync_mod.build_clone_cmd(
                        target=target, origin_url=origin, branch=branch, repo_basename=basename,
                    ))
                    entry["origin"] = origin
                files = sync_mod.uncommitted_files(repo_path)
                wip_cmd = sync_mod.build_rsync_cmd(
                    target=target, local_root=repo_path, files=files, repo_basename=basename,
                )
                if wip_cmd:
                    _run_or_raise(wip_cmd, stdin="\n".join(files) + "\n")
                    entry["wip_files"] = len(files)
            else:
                # Not a git repo — rsync everything except hard-block patterns.
                cmd = sync_mod.build_rsync_ignored_cmd(
                    target=target, local_root=repo_path.parent, include_path=repo_path.name, repo_basename=basename,
                )
                _run_or_raise(cmd)
                entry["mode"] = "rsync_full"
            for path in include_ignored:
                cmd = sync_mod.build_rsync_ignored_cmd(
                    target=target, local_root=repo_path, include_path=path, repo_basename=basename,
                )
                _run_or_raise(cmd)
            synced_repos.append(entry)

        record = state_mod.VastaiInstanceState(
            alias=chosen_alias,
            instance_id=instance_id,
            ssh_host=instance.ssh_host,
            ssh_port=instance.ssh_port,
            ssh_user=instance.ssh_user,
            ssh_key_path=str(ssh_key),
            ssh_config_alias=host_alias,
            repo_paths=[str(p) for p in repo],
            image=image,
            gpu=gpu,
            disk_gb=disk,
            region=region,
        )
        state_mod.save_state(record)

        payload = {
            "alias": chosen_alias,
            "ssh_alias": host_alias,
            "instance_id": instance_id,
            "ssh_host": instance.ssh_host,
            "ssh_port": instance.ssh_port,
            "offer": summary,
            "repos": synced_repos,
            "vscode": f"code --remote ssh-remote+{host_alias} {target.remote_root}",
            "ssh": f"ssh {host_alias}",
        }
        success_message = (
            f"[green]Ready.[/green] Connect: [cyan]ssh {host_alias}[/cyan]\n"
            f"VS Code: [cyan]{payload['vscode']}[/cyan]"
        )
        _emit(payload, json_output=json_output, success_message=success_message)
    except TaiError:
        raise
    except Exception as exc:
        raise TaiError(f"vastai up failed: {exc}", hint="Re-run with --verbose for a traceback.") from exc


@app.command("down")
def down(
    alias: Optional[str] = typer.Argument(None, help="Alias to tear down. Omit with --all."),
    all_: bool = typer.Option(False, "--all", help="Tear down every recorded alias."),
    keep_key: bool = typer.Option(False, "--keep-key", help="Don't delete the generated SSH key."),
    shred: bool = typer.Option(
        True, "--shred/--no-shred",
        help="Wipe secrets (~/.claude, ~/.codex, .env, repo trees) on the box "
             "before destroying. --no-shred skips the SSH round-trip "
             "(useful if the box is already unreachable).",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Destroy instance(s) and clean up local config."""
    aliases = state_mod.list_aliases()
    if all_:
        targets = aliases
    elif alias is None:
        if len(aliases) == 1:
            targets = aliases
        else:
            raise TaiError(
                "Specify an alias or pass --all.",
                hint=f"Known aliases: {aliases or '(none)'}",
            )
    else:
        targets = [state_mod.normalise_alias(alias)]

    if not targets:
        _emit({"removed": []}, json_output=json_output, success_message="Nothing to clean up.")
        return

    if not yes:
        prompt = f"Destroy {len(targets)} instance(s) ({', '.join(targets)})? This cannot be undone."
        if not _confirm(prompt, assume_yes=False):
            raise TaiError("Aborted by user.")

    provisioner = provision_mod.Provisioner()
    removed: list[dict] = []
    for a in targets:
        record = state_mod.load_state(a)
        if shred:
            host_alias = record.ssh_config_alias or ssh_config_mod.host_alias(a)
            remote_paths = bootstrap_mod.shred_paths_for_state(
                repo_paths=record.repo_paths,
                remote_repo_root=record.remote_repo_root,
            )
            shred_cmd = bootstrap_mod.build_remote_shred_command(
                ssh_alias=host_alias, remote_paths=remote_paths,
            )
            shred_result = subprocess.run(
                shred_cmd, capture_output=True, text=True, check=False,
            )
            if shred_result.returncode != 0:
                err_console.print(
                    f"[yellow]Warning:[/yellow] remote shred failed for {a!r} "
                    f"(continuing with destroy). "
                    f"{(shred_result.stderr or shred_result.stdout or '').strip()[:200]}"
                )
        try:
            provisioner.destroy_instance(record.instance_id)
        except TaiError as exc:
            err_console.print(f"[yellow]Warning:[/yellow] {exc} (continuing cleanup)")
        ssh_config_mod.remove_block(a)
        if not keep_key and record.ssh_key_path:
            for suffix in ("", ".pub"):
                path = Path(record.ssh_key_path + suffix)
                if path.exists():
                    path.unlink()
        state_mod.delete_state(a)
        removed.append({"alias": a, "instance_id": record.instance_id})

    _emit(
        {"removed": removed},
        json_output=json_output,
        success_message=f"Removed {len(removed)} instance(s).",
    )


@app.command("list")
def list_(json_output: bool = typer.Option(False, "--json", help="Emit JSON.")) -> None:
    """List recorded aliases."""
    aliases = state_mod.list_aliases()
    rows = [state_mod.load_state(a).model_dump() for a in aliases]
    if json_output:
        console.print_json(jsonlib.dumps(rows))
        return
    if not rows:
        console.print("[dim]No vastai instances recorded.[/dim]")
        return
    table = Table(title="vastai instances")
    table.add_column("alias")
    table.add_column("instance")
    table.add_column("gpu")
    table.add_column("ssh")
    for row in rows:
        table.add_row(
            row["alias"],
            str(row["instance_id"]),
            row["gpu"],
            f"{row['ssh_user']}@{row['ssh_host']}:{row['ssh_port']}",
        )
    console.print(table)


@app.command("status")
def status_cmd(
    alias: str = typer.Argument(..., help="Alias to inspect."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
) -> None:
    """Show a single alias's recorded state."""
    record = state_mod.load_state(alias)
    if json_output:
        console.print_json(jsonlib.dumps(record.model_dump()))
        return
    console.print(record.model_dump())

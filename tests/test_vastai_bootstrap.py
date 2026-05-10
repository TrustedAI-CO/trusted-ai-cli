"""Bootstrap script + cred copy planning."""

from __future__ import annotations

from pathlib import Path

from tai.core.vastai import bootstrap


def test_install_script_installs_uv_and_tai():
    s = bootstrap.REMOTE_INSTALL_SCRIPT
    assert "astral.sh/uv/install.sh" in s
    assert "trusted-ai-cli" in s
    assert "@anthropic-ai/claude-code" in s
    assert "@openai/codex" in s
    assert "tai claude setup-skills --force" in s
    assert "tai codex  setup-skills --force" in s
    assert "set -euo pipefail" in s


def test_install_script_seeds_github_host_key():
    s = bootstrap.REMOTE_INSTALL_SCRIPT
    assert "ssh-keyscan" in s
    assert "github.com" in s
    assert "gitlab.com" in s


def test_install_script_upgrades_node_when_too_old():
    s = bootstrap.REMOTE_INSTALL_SCRIPT
    assert "deb.nodesource.com/setup_20.x" in s
    assert "node -v" in s


def test_install_script_removes_libnode_dev_before_nodesource_install():
    # Ubuntu 22.04 ships libnode-dev which conflicts with NodeSource's nodejs.
    s = bootstrap.REMOTE_INSTALL_SCRIPT
    assert "libnode-dev" in s
    assert s.index("libnode-dev") < s.index("setup_20.x")


def test_render_install_script_uses_wheel_path_when_provided():
    s = bootstrap.render_install_script("/tmp/trusted_ai_cli-0.25.0-py3-none-any.whl")
    assert 'uv tool install --force "/tmp/trusted_ai_cli-0.25.0-py3-none-any.whl"' in s
    # No PyPI fallback when shipping a wheel.
    assert "pip install --user --upgrade trusted-ai-cli" not in s


def test_render_install_script_falls_back_to_pypi_without_wheel():
    s = bootstrap.render_install_script(None)
    assert "uv tool install --force trusted-ai-cli" in s
    assert "pip install --user --upgrade trusted-ai-cli" in s


def test_find_tai_source_root_walks_up(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "trusted-ai-cli"\n')
    assert bootstrap.find_tai_source_root(nested) == tmp_path.resolve()


def test_find_tai_source_root_skips_unrelated_pyproject(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "other-pkg"\n')
    assert bootstrap.find_tai_source_root(nested) is None


def test_build_wheel_upload_commands_returns_remote_path(tmp_path):
    wheel = tmp_path / "trusted_ai_cli-0.25.0-py3-none-any.whl"
    wheel.write_bytes(b"")
    cmds, remote = bootstrap.build_wheel_upload_commands(
        ssh_alias="vastai-quick-gpu", wheel_path=wheel,
    )
    assert remote == "/tmp/trusted_ai_cli-0.25.0-py3-none-any.whl"
    assert any("mkdir" in c for c in cmds)
    assert any(str(wheel) in part for c in cmds for part in c)


def test_plan_cred_copy_disabled_returns_empty(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / ".credentials.json").write_text("{}")
    assert bootstrap.plan_cred_copy(enabled=False, home=tmp_path) == []


def test_plan_cred_copy_includes_only_existing_files(tmp_path):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "auth.json").write_text("{}")
    plans = bootstrap.plan_cred_copy(enabled=True, home=tmp_path)
    assert len(plans) == 1
    assert plans[0].local == tmp_path / ".codex" / "auth.json"
    assert plans[0].remote == "~/.codex/auth.json"
    assert plans[0].is_secret is True


def test_build_install_command_pipes_via_ssh():
    cmd = bootstrap.build_install_command("vastai-quick-gpu")
    assert "vastai-quick-gpu" in cmd
    assert cmd[-2:] == ["bash", "-s"]


def test_build_cred_copy_commands(tmp_path):
    plan = bootstrap.CredCopyPlan(local=tmp_path / "auth.json", remote="~/.codex/auth.json")
    cmds = bootstrap.build_cred_copy_commands(ssh_alias="vastai-quick-gpu", plans=[plan])
    assert len(cmds) == 3
    # mkdir, scp, chmod
    assert "mkdir" in cmds[0]
    assert any("scp" in part for part in cmds[1][:1])
    assert "chmod" in cmds[2]
    assert "600" in cmds[2]


def test_shred_paths_for_state_uses_basename_under_remote_root():
    paths = bootstrap.shred_paths_for_state(
        repo_paths=["/Users/jack/Desktop/TGR_Project", "/tmp/other"],
        remote_repo_root="/root",
    )
    assert paths == ["/root/TGR_Project", "/root/other"]


def test_build_remote_shred_command_wipes_creds_wheel_and_repos():
    cmd = bootstrap.build_remote_shred_command(
        ssh_alias="vastai-quick-gpu",
        remote_paths=["/root/TGR_Project"],
    )
    # Short ConnectTimeout so unreachable boxes fail fast.
    assert "ConnectTimeout=10" in cmd
    assert "BatchMode=yes" in cmd
    assert "vastai-quick-gpu" in cmd
    script = cmd[-1]
    # `~` and glob must be left unquoted so bash expands them.
    assert '"$HOME/.claude"' in script
    assert '"$HOME/.codex"' in script
    assert "/tmp/trusted_ai_cli-*.whl" in script
    assert "/root/TGR_Project" in script
    # Failures during shred must not abort the destroy.
    assert "set +e" in script
    assert "exit 0" in script


def test_build_remote_shred_command_honors_custom_timeout():
    cmd = bootstrap.build_remote_shred_command(
        ssh_alias="vastai-quick-gpu",
        remote_paths=[],
        connect_timeout_s=3,
    )
    assert "ConnectTimeout=3" in cmd

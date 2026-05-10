"""Smoke tests for `tai vastai` Typer commands.

Heavy paths (offers/provision/sync) are mocked at the module level —
this test suite only validates wiring, JSON shape, and the empty-state
branches.
"""

from __future__ import annotations

import json

import pytest

from tai.commands import vastai as vastai_cmd
from tai.core.vastai import state as state_mod


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
    return tmp_path


def test_list_empty(runner, isolated_state):
    result = runner.invoke(vastai_cmd.app, ["list", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_down_no_aliases(runner, isolated_state):
    result = runner.invoke(vastai_cmd.app, ["down", "--all", "--yes", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"removed": []}


def test_status_unknown_alias_errors(runner, isolated_state):
    result = runner.invoke(vastai_cmd.app, ["status", "missing"])
    # TaiError is raised; CliRunner returns it as exit_code != 0.
    assert result.exit_code != 0


def test_list_prints_recorded(runner, isolated_state):
    record = state_mod.VastaiInstanceState(
        alias="quick-gpu",
        instance_id=123,
        ssh_host="ssh.vast.ai",
        ssh_port=4242,
        ssh_key_path="/tmp/k",
        ssh_config_alias="vastai-quick-gpu",
        gpu="RTX_5090",
    )
    state_mod.save_state(record, base=isolated_state)
    result = runner.invoke(vastai_cmd.app, ["list", "--json"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0]["instance_id"] == 123


def test_down_requires_alias_when_multiple(runner, isolated_state):
    for a in ["one", "two"]:
        state_mod.save_state(
            state_mod.VastaiInstanceState(
                alias=a, instance_id=1, ssh_host="x", ssh_port=1,
                ssh_key_path="/tmp/k", ssh_config_alias=f"vastai-{a}",
            ),
            base=isolated_state,
        )
    result = runner.invoke(vastai_cmd.app, ["down", "--yes", "--json"])
    assert result.exit_code != 0

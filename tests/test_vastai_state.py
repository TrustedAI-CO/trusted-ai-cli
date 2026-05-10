"""State file roundtrip and alias allocation."""

from __future__ import annotations

import pytest

from tai.core.errors import TaiError
from tai.core.vastai import state


def _make(alias: str = "quick-gpu", instance_id: int = 12345) -> state.VastaiInstanceState:
    return state.VastaiInstanceState(
        alias=alias,
        instance_id=instance_id,
        ssh_host="ssh.vast.ai",
        ssh_port=12345,
        ssh_key_path="/tmp/key",
        ssh_config_alias=f"vastai-{alias}",
    )


def test_roundtrip(tmp_path):
    s = _make()
    state.save_state(s, base=tmp_path)
    loaded = state.load_state("quick-gpu", base=tmp_path)
    assert loaded.instance_id == 12345
    assert loaded.ssh_host == "ssh.vast.ai"


def test_partial_save_without_ssh_details(tmp_path):
    # Right after `vastai create instance` we have an id but no ssh
    # endpoint yet. State must be persistable so a later failure is
    # recoverable via `tai vastai down`.
    partial = state.VastaiInstanceState(
        alias="quick-gpu",
        instance_id=99,
        ssh_key_path="/tmp/key",
        ssh_config_alias="vastai-quick-gpu",
    )
    state.save_state(partial, base=tmp_path)
    loaded = state.load_state("quick-gpu", base=tmp_path)
    assert loaded.instance_id == 99
    assert loaded.ssh_host == ""
    assert loaded.ssh_port == 0


def test_load_missing_raises(tmp_path):
    with pytest.raises(TaiError):
        state.load_state("nope", base=tmp_path)


def test_delete_returns_true_when_present(tmp_path):
    state.save_state(_make(), base=tmp_path)
    assert state.delete_state("quick-gpu", base=tmp_path) is True
    assert state.delete_state("quick-gpu", base=tmp_path) is False


def test_list_aliases_sorted(tmp_path):
    for a in ["b-box", "a-box", "c-box"]:
        state.save_state(_make(alias=a), base=tmp_path)
    assert state.list_aliases(tmp_path) == ["a-box", "b-box", "c-box"]


def test_normalise_alias_strips_unsafe():
    assert state.normalise_alias("Quick GPU!") == "quick-gpu"
    assert state.normalise_alias("  --foo--  ") == "foo"


def test_normalise_alias_rejects_empty():
    with pytest.raises(TaiError):
        state.normalise_alias("!!!")


def test_next_available_alias_suffixes(tmp_path):
    state.save_state(_make(alias="quick-gpu"), base=tmp_path)
    state.save_state(_make(alias="quick-gpu-2"), base=tmp_path)
    assert state.next_available_alias("quick-gpu", base=tmp_path) == "quick-gpu-3"


def test_next_available_alias_returns_requested_when_free(tmp_path):
    assert state.next_available_alias("fresh", base=tmp_path) == "fresh"

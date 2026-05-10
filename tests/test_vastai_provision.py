"""Provision flow with mocked vastai/ssh-keygen subprocesses."""

from __future__ import annotations

import json
import subprocess

import pytest

from tai.core.errors import TaiError
from tai.core.vastai import provision


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[str]] = []

    def __call__(self, cmd):
        self.calls.append(list(cmd))
        if not self.responses:
            raise AssertionError(f"Unexpected extra command: {cmd}")
        nxt = self.responses.pop(0)
        if callable(nxt):
            nxt = nxt(cmd)
        returncode, stdout, stderr = nxt
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


@pytest.fixture
def vastai_path(monkeypatch):
    monkeypatch.setattr(provision, "_ensure_vastai", lambda: "/usr/bin/vastai")
    return "/usr/bin/vastai"


def test_create_instance_returns_new_contract(vastai_path):
    runner = FakeRunner([
        (0, json.dumps({"success": True, "new_contract": 99}), ""),
    ])
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None)
    new_id = p.create_instance(
        offer_id=33438337,
        image="pytorch/pytorch:latest",
        disk_gb=512,
        alias="quick-gpu",
    )
    assert new_id == 99
    assert "create" in runner.calls[0]
    assert "instance" in runner.calls[0]
    assert "33438337" in runner.calls[0]
    assert "--ssh" in runner.calls[0]


def test_create_instance_failure_raises(vastai_path):
    runner = FakeRunner([(0, json.dumps({"success": False, "msg": "no_capacity"}), "")])
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None)
    with pytest.raises(TaiError):
        p.create_instance(offer_id=1, image="img", disk_gb=10, alias="a")


def test_attach_ssh_key_passes_pubkey(vastai_path):
    runner = FakeRunner([(0, "", "")])
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None)
    p.attach_ssh_key(99, "ssh-ed25519 AAAA user")
    cmd = runner.calls[0]
    assert cmd[1:4] == ["attach", "ssh", "99"]
    assert cmd[4] == "ssh-ed25519 AAAA user"


def test_wait_for_ssh_returns_when_running(vastai_path):
    runner = FakeRunner([
        (0, json.dumps({"actual_status": "loading"}), ""),
        (0, json.dumps({"actual_status": "running", "ssh_host": "ssh1.vast.ai", "ssh_port": 12345}), ""),
    ])
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None, poll_interval_s=0.0)
    inst = p.wait_for_ssh(99)
    assert inst.ssh_host == "ssh1.vast.ai"
    assert inst.ssh_port == 12345


def test_wait_for_ssh_times_out(vastai_path):
    def loading(cmd):
        return (0, json.dumps({"actual_status": "loading"}), "")
    runner = FakeRunner([loading] * 5)
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None, poll_interval_s=0.0, max_wait_s=0.0)
    with pytest.raises(TaiError):
        p.wait_for_ssh(99)


def test_destroy_instance_invokes_destroy(vastai_path):
    runner = FakeRunner([(0, "", "")])
    p = provision.Provisioner(runner=runner, sleeper=lambda _: None)
    p.destroy_instance(99)
    # `-y` must be present — without it vastai prompts and exits 0 as a no-op.
    assert runner.calls[0][1:] == ["destroy", "instance", "99", "-y"]


def test_generate_ssh_key_creates_files(tmp_path):
    pub = tmp_path / "vastai_quick-gpu_ed25519.pub"
    priv = tmp_path / "vastai_quick-gpu_ed25519"

    def fake_runner(cmd):
        priv.write_text("PRIVKEY")
        pub.write_text("ssh-ed25519 AAAA tai-vastai-quick-gpu")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    out = provision.generate_ssh_key("quick-gpu", base=tmp_path, runner=fake_runner)
    assert out == priv
    assert priv.exists()


def test_generate_ssh_key_skips_when_present(tmp_path):
    priv = tmp_path / "vastai_quick-gpu_ed25519"
    priv.write_text("EXISTING")
    runner = FakeRunner([])  # would raise if invoked
    out = provision.generate_ssh_key("quick-gpu", base=tmp_path, runner=runner)
    assert out == priv
    assert priv.read_text() == "EXISTING"
    assert runner.calls == []

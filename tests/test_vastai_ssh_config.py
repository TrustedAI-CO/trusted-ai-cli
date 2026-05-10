"""SSH config block insert/replace/remove."""

from __future__ import annotations

from tai.core.vastai import ssh_config


def _block(alias: str = "quick-gpu", port: int = 12345) -> str:
    return ssh_config.render_block(
        alias=alias,
        hostname="ssh.vast.ai",
        port=port,
        user="root",
        identity_file="/tmp/key",
    )


def test_render_block_contains_required_directives():
    rendered = _block()
    assert "Host vastai-quick-gpu" in rendered
    assert "HostName ssh.vast.ai" in rendered
    assert "Port 12345" in rendered
    assert "ForwardAgent yes" in rendered
    assert rendered.startswith("# >>> tai vastai: quick-gpu >>>")


def test_upsert_creates_file(tmp_path):
    cfg = tmp_path / "config"
    ssh_config.upsert_block(_block(), alias="quick-gpu", config_path=cfg)
    assert "Host vastai-quick-gpu" in cfg.read_text()


def test_upsert_replaces_existing_block(tmp_path):
    cfg = tmp_path / "config"
    ssh_config.upsert_block(_block(port=1111), alias="quick-gpu", config_path=cfg)
    ssh_config.upsert_block(_block(port=2222), alias="quick-gpu", config_path=cfg)
    text = cfg.read_text()
    assert text.count("Host vastai-quick-gpu") == 1
    assert "Port 2222" in text
    assert "Port 1111" not in text


def test_upsert_preserves_unrelated_content(tmp_path):
    cfg = tmp_path / "config"
    cfg.write_text("Host other\n    HostName other.example\n")
    ssh_config.upsert_block(_block(), alias="quick-gpu", config_path=cfg)
    text = cfg.read_text()
    assert "Host other" in text
    assert "Host vastai-quick-gpu" in text


def test_remove_block(tmp_path):
    cfg = tmp_path / "config"
    cfg.write_text("Host other\n    HostName other.example\n")
    ssh_config.upsert_block(_block(), alias="quick-gpu", config_path=cfg)
    assert ssh_config.remove_block("quick-gpu", config_path=cfg) is True
    text = cfg.read_text()
    assert "vastai-quick-gpu" not in text
    assert "Host other" in text


def test_remove_block_no_op_when_absent(tmp_path):
    cfg = tmp_path / "config"
    cfg.write_text("Host other\n    HostName other.example\n")
    assert ssh_config.remove_block("quick-gpu", config_path=cfg) is False


def test_remove_block_no_op_when_file_missing(tmp_path):
    assert ssh_config.remove_block("quick-gpu", config_path=tmp_path / "missing") is False

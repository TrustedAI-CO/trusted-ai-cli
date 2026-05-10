"""Offer query construction, parsing, and selection."""

from __future__ import annotations

import json
import subprocess

import pytest

from tai.core.errors import TaiError
from tai.core.vastai import offers


def _make_run(stdout: str = "[]", returncode: int = 0, stderr: str = ""):
    def run(cmd):
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    return run


def test_query_string_includes_required_filters():
    q = offers.OfferQuery(gpu="RTX 5090", disk_gb=512, region="us")
    text = q.to_query_string()
    assert "gpu_name=RTX_5090" in text
    assert "disk_space>=512" in text
    assert "geolocation in [US]" in text
    assert "verified=true" in text
    assert "rentable=true" in text


def test_query_string_omits_geolocation_for_any():
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="any")
    assert "geolocation" not in q.to_query_string()


def test_query_string_accepts_two_letter_country():
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="jp")
    assert "geolocation in [JP]" in q.to_query_string()


def test_query_string_accepts_csv_region():
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="us,ca,mx")
    assert "geolocation in [US,CA,MX]" in q.to_query_string()


def test_query_string_rejects_unknown_region():
    with pytest.raises(TaiError):
        offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="atlantis").to_query_string()


def test_pick_cheapest_picks_lowest_dph():
    sample = [
        {"id": 1, "dph_total": 0.5},
        {"id": 2, "dph_total": 0.3},
        {"id": 3, "dph_total": 0.4},
    ]
    assert offers.pick_cheapest(sample)["id"] == 2


def test_pick_cheapest_empty_raises():
    with pytest.raises(TaiError):
        offers.pick_cheapest([])


def test_summarise_offer_strips_geolocation_prefix():
    summary = offers.summarise_offer({
        "id": 99,
        "gpu_name": "RTX 5090",
        "num_gpus": 1,
        "gpu_ram": 32607,
        "disk_space": 678.75,
        "dph_total": 0.29,
        "geolocation": ", US",
        "cuda_max_good": 13.0,
        "reliability2": 0.99,
    })
    assert summary["geolocation"] == "US"
    assert summary["gpu_ram_gb"] == 31.8
    assert summary["disk_space_gb"] == 678.8
    assert summary["reliability"] == 0.99


def test_search_offers_returns_parsed_list(monkeypatch):
    monkeypatch.setattr(offers, "_ensure_vastai", lambda: "/usr/bin/vastai")
    payload = [{"id": 1, "dph_total": 0.5}]
    runner = _make_run(stdout=json.dumps(payload))
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="any")
    result = offers.search_offers(q, runner=runner)
    assert result == payload


def test_search_offers_propagates_runner_error(monkeypatch):
    monkeypatch.setattr(offers, "_ensure_vastai", lambda: "/usr/bin/vastai")
    runner = _make_run(returncode=1, stderr="boom")
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="any")
    with pytest.raises(TaiError) as exc:
        offers.search_offers(q, runner=runner)
    assert "boom" in (exc.value.hint or "")


def test_search_offers_rejects_non_list(monkeypatch):
    monkeypatch.setattr(offers, "_ensure_vastai", lambda: "/usr/bin/vastai")
    runner = _make_run(stdout='{"error":"x"}')
    q = offers.OfferQuery(gpu="RTX_5090", disk_gb=100, region="any")
    with pytest.raises(TaiError):
        offers.search_offers(q, runner=runner)

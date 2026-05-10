"""Build vast.ai offer queries and pick the cheapest match.

We expose pure functions over the JSON output of ``vastai search offers
--raw`` so tests don't need a network or the binary. The runtime side
(actually invoking ``vastai``) lives in :func:`search_offers`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from tai.core.errors import TaiError

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]

# Curated regions → ISO country code lists understood by vast.ai's
# `geolocation in [...]` filter. Keep this small; users with stricter
# requirements can pass --region with a custom comma-separated list.
REGION_PRESETS: dict[str, list[str]] = {
    "any": [],
    "us": ["US"],
    "na": ["US", "CA"],
    "eu": ["DE", "FR", "NL", "SE", "FI", "GB", "IE", "IT", "ES", "PL", "CH", "AT", "BE", "NO", "DK", "PT"],
    "asia": ["JP", "SG", "KR", "TW", "HK"],
}


@dataclass(frozen=True)
class OfferQuery:
    gpu: str
    disk_gb: int
    region: str = "any"
    min_reliability: float = 0.95
    num_gpus: int = 1

    def to_query_string(self) -> str:
        parts: list[str] = [
            f"gpu_name={_format_gpu(self.gpu)}",
            f"num_gpus={self.num_gpus}",
            f"disk_space>={self.disk_gb}",
            f"reliability>{self.min_reliability}",
            "verified=true",
            "rentable=true",
            "rented=false",
        ]
        countries = _resolve_region(self.region)
        if countries:
            parts.append(f"geolocation in [{','.join(countries)}]")
        return " ".join(parts)


def _format_gpu(gpu: str) -> str:
    """vast.ai expects underscores in multi-word GPU names (RTX_5090)."""
    return gpu.strip().replace(" ", "_")


def _resolve_region(region: str) -> list[str]:
    key = region.strip().lower()
    if key in REGION_PRESETS:
        return REGION_PRESETS[key]
    if "," in region:
        return [c.strip().upper() for c in region.split(",") if c.strip()]
    if len(key) == 2:
        return [key.upper()]
    raise TaiError(
        f"Unknown region preset: {region!r}",
        hint=f"Use one of {sorted(REGION_PRESETS)} or a comma-separated country code list.",
    )


def pick_cheapest(offers: list[dict]) -> dict:
    """Return the offer with the lowest ``dph_total``.

    Raises TaiError if the list is empty.
    """
    if not offers:
        raise TaiError(
            "No vast.ai offers matched your query",
            hint="Loosen GPU/disk/region constraints or check `vastai search offers` directly.",
        )
    return min(offers, key=lambda o: float(o.get("dph_total", float("inf"))))


def summarise_offer(offer: dict) -> dict:
    """Compact, JSON-friendly view used in confirmation prompts and output."""
    geo = (offer.get("geolocation") or "").lstrip(", ").strip()
    return {
        "id": offer.get("id"),
        "gpu_name": offer.get("gpu_name"),
        "num_gpus": offer.get("num_gpus"),
        "gpu_ram_gb": _round_or_none(offer.get("gpu_ram"), 1024),
        "disk_space_gb": _round_or_none(offer.get("disk_space")),
        "dph_total": offer.get("dph_total"),
        "geolocation": geo,
        "cuda_max_good": offer.get("cuda_max_good"),
        "reliability": offer.get("reliability2") or offer.get("reliability"),
    }


def _round_or_none(value, divisor: float = 1.0):
    if value is None:
        return None
    try:
        return round(float(value) / divisor, 1)
    except (TypeError, ValueError):
        return None


def _default_runner(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _ensure_vastai() -> str:
    binary = shutil.which("vastai")
    if not binary:
        raise TaiError(
            "vastai CLI not found on PATH",
            hint="Install it: `pipx install vastai` or `pip install --user vastai`.",
        )
    return binary


def search_offers(query: OfferQuery, *, runner: Runner | None = None) -> list[dict]:
    """Run `vastai search offers` and return parsed offers."""
    binary = _ensure_vastai()
    runner = runner or _default_runner
    cmd = [binary, "search", "offers", "--raw", "-o", "dph_total", query.to_query_string()]
    result = runner(cmd)
    if result.returncode != 0:
        raise TaiError(
            "vastai search offers failed",
            hint=(result.stderr or result.stdout or "").strip() or "Run with --verbose for details.",
        )
    try:
        offers = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise TaiError(
            "Could not parse vastai output",
            hint=f"Got: {result.stdout[:200]!r}",
        ) from exc
    if not isinstance(offers, list):
        raise TaiError("Unexpected vastai response shape", hint="Expected a JSON array of offers.")
    return offers

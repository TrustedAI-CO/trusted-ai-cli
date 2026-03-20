"""Profile-based configuration with XDG Base Directory support.

Config precedence (highest → lowest):
  flags → env vars (TAI_*) → project config → user config (~/.config/tai/config.toml)
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomli_w
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from tai.core.errors import ConfigError

# XDG Base Directory — https://specifications.freedesktop.org/basedir-spec/latest/
_XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = _XDG_CONFIG_HOME / "tai"
CONFIG_FILE = CONFIG_DIR / "config.toml"
PROJECT_CONFIG_FILE = Path(".tai.toml")


# Public by design — GCP Desktop app client IDs are embedded in OAuth redirect URLs.
_DEFAULT_CLIENT_ID = "93557845654-0engg5khklcoa1qc53eu33hguvc37gpn.apps.googleusercontent.com"
_DEFAULT_COMPANY_DOMAIN = "trusted-ai.co"


class ProfileConfig(BaseModel):
    api_base_url: str = "https://api.trusted-ai.internal"
    ai_model: str = "claude-sonnet-4-6"
    company_domain: str = _DEFAULT_COMPANY_DOMAIN
    oauth_client_id: str = _DEFAULT_CLIENT_ID
    # Desktop OAuth apps use PKCE for security; client_secret is not required.
    # Override via: tai config set oauth_client_secret <SECRET>
    oauth_client_secret: str = ""
    timeout_seconds: int = 30

    model_config = {"extra": "allow"}


class TaiConfig(BaseModel):
    current_profile: str = "default"
    profiles: dict[str, ProfileConfig] = Field(
        default_factory=lambda: {"default": ProfileConfig()}
    )

    def active(self) -> ProfileConfig:
        return self.profiles.get(self.current_profile, ProfileConfig())


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def load_config(profile_override: str | None = None) -> TaiConfig:
    """Load config merging user config + optional project config."""
    user_data = _load_toml(CONFIG_FILE)
    project_data = _load_toml(PROJECT_CONFIG_FILE)

    # Project overrides user for any matching keys
    merged = {**user_data, **project_data}

    # Deep-merge profiles
    user_profiles = user_data.get("profiles", {})
    project_profiles = project_data.get("profiles", {})
    merged_profiles: dict[str, Any] = {}
    for name in set(user_profiles) | set(project_profiles):
        merged_profiles[name] = {**user_profiles.get(name, {}), **project_profiles.get(name, {})}

    if merged_profiles:
        merged["profiles"] = merged_profiles

    config = TaiConfig.model_validate(merged)

    if profile_override:
        if profile_override not in config.profiles:
            raise ConfigError(
                f"Profile '{profile_override}' not found",
                hint=f"Run: tai config list-profiles",
            )
        config.current_profile = profile_override

    return config


@dataclass(frozen=True)
class BrandColors:
    """Brand color values loaded from brand.toml."""

    company_name: str = "TrustedAI"
    company_tagline: str | None = None
    primary: str | None = None
    secondary: str | None = None
    accent: str | None = None


def load_brand_colors(brand_toml: Path) -> BrandColors:
    """Load brand colors from a brand.toml file.

    Returns defaults if the file is missing or malformed.
    """
    if not brand_toml.is_file():
        return BrandColors()

    try:
        data = _load_toml(brand_toml)
    except Exception:
        return BrandColors()

    company = data.get("company", {})
    colors = data.get("colors", {})

    return BrandColors(
        company_name=company.get("name", "TrustedAI") or "TrustedAI",
        company_tagline=company.get("tagline") or None,
        primary=colors.get("primary") or None,
        secondary=colors.get("secondary") or None,
        accent=colors.get("accent") or None,
    )


def save_config(config: TaiConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = config.model_dump()
    with CONFIG_FILE.open("wb") as f:
        tomli_w.dump(data, f)

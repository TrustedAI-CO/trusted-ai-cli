"""Vast.ai quick-GPU provisioning helpers.

Each module owns one stage of the lifecycle:
  state       — on-disk JSON per alias under ~/.config/tai/vastai/
  ssh_config  — idempotent block writer for ~/.ssh/config
  offers      — search/parse vastai offers
  provision   — create instance, attach SSH key, wait for ready
  sync        — git clone + rsync uncommitted/ignored paths
  bootstrap   — remote install script (uv, claude, codex, tai)
"""

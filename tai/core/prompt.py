"""Reusable interactive prompt utilities."""

from __future__ import annotations

import sys
from typing import Callable, TypeVar

from InquirerPy import inquirer

T = TypeVar("T")


def is_interactive() -> bool:
    """Return True when stdin is a real TTY (not piped / CI / agent shell)."""
    return sys.stdin.isatty()


def make_completer(items: list[str], max_shown: int = 10) -> Callable[[str], list[str]]:
    """Return a filter function: given typed text, return matching items (max *max_shown*).

    Useful for custom completion logic outside of questionary (e.g. tests, other UIs).
    - Empty text → first *max_shown* items
    - Non-empty text → case-insensitive mid-string match, capped at *max_shown*
    """
    def complete(text: str) -> list[str]:
        if not text:
            return items[:max_shown]
        needle = text.lower()
        return [item for item in items if needle in item.lower()][:max_shown]

    return complete


def search_select(
    message: str,
    items: list[T],
    label_fn: Callable[[T], str],
    max_shown: int = 10,
) -> T | None:
    """Interactive fuzzy search — returns chosen item or None if cancelled.

    All items are searchable; only *max_shown* rows are visible at once.

    Args:
        message:   Prompt label shown to the user.
        items:     Any list of objects to choose from.
        label_fn:  Extracts the display string from each item.
        max_shown: Number of rows visible in the dropdown at once.
    """
    label_to_item = {label_fn(item): item for item in items}
    pool = list(label_to_item.keys())

    answer = inquirer.fuzzy(
        message=message,
        choices=pool,
        max_height=max_shown,
    ).execute()

    if answer is None:
        return None
    return label_to_item.get(answer)

"""Reusable interactive prompt utilities."""

from __future__ import annotations

from typing import Callable, TypeVar

import questionary
from InquirerPy import inquirer

T = TypeVar("T")


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

    Args:
        message:   Prompt label shown to the user.
        items:     Any list of objects to choose from.
        label_fn:  Extracts the display string from each item.
        max_shown: Maximum number of items in the autocomplete pool.
    """
    label_to_item = {label_fn(item): item for item in items}
    # questionary calls `choices` with no args to populate the list;
    # it handles character-by-character filtering internally (match_middle).
    # We cap the pool at max_shown so the dropdown never exceeds that count.
    pool = list(label_to_item.keys())[:max_shown]

    answer = inquirer.fuzzy(
        message=message,
        choices=pool,
        max_height="40%",
    ).execute()

    if answer is None:
        return None
    return label_to_item.get(answer)

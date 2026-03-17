"""Reusable interactive prompt utilities."""

from __future__ import annotations

from typing import Callable, TypeVar

import questionary

T = TypeVar("T")


def make_completer(items: list[str], max_shown: int = 10) -> Callable[[str], list[str]]:
    """Return a completion function that filters *items* by typed text.

    - Empty input → first *max_shown* items (show everything up to limit)
    - Non-empty input → case-insensitive mid-string match, capped at *max_shown*
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
        message:  Prompt label shown to the user.
        items:    Any list of objects to choose from.
        label_fn: Extracts the display string from each item.
        max_shown: Maximum number of options visible at once.
    """
    label_to_item = {label_fn(item): item for item in items}
    completer = make_completer(list(label_to_item.keys()), max_shown=max_shown)

    answer = questionary.autocomplete(
        message,
        choices=completer,
        match_middle=True,
        style=questionary.Style([("answer", "fg:#00aaff bold")]),
    ).ask()

    if answer is None:
        return None
    return label_to_item.get(answer)

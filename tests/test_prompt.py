"""Tests for tai/core/prompt.py — reusable interactive search."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tai.core.prompt import search_select, make_completer


# ── make_completer ────────────────────────────────────────────────────────────


def test_completer_empty_input_returns_all_up_to_max():
    items = [f"Project {i}" for i in range(15)]
    complete = make_completer(items, max_shown=10)
    assert complete("") == items[:10]


def test_completer_filters_by_keyword():
    items = ["Video Research", "SafeChat Improvement", "Blog Migration"]
    complete = make_completer(items)
    assert complete("video") == ["Video Research"]


def test_completer_filters_case_insensitive():
    items = ["Video Research", "SafeChat Improvement"]
    complete = make_completer(items)
    assert complete("VIDEO") == ["Video Research"]


def test_completer_matches_middle_of_string():
    items = ["Video Research", "SafeChat Improvement", "Research Blog"]
    complete = make_completer(items)
    results = complete("search")
    assert "Video Research" in results
    assert "Research Blog" in results
    assert "SafeChat Improvement" not in results


def test_completer_respects_max_shown():
    items = [f"Alpha Project {i}" for i in range(20)]
    complete = make_completer(items, max_shown=5)
    assert len(complete("alpha")) == 5


def test_completer_returns_empty_when_no_match():
    items = ["Video Research", "SafeChat"]
    complete = make_completer(items)
    assert complete("zzz") == []


# ── search_select ─────────────────────────────────────────────────────────────


def _mock_fuzzy(return_value):
    m = MagicMock()
    m.execute.return_value = return_value
    return m


def test_search_select_returns_chosen_item():
    projects = [
        {"id": "abc", "name": "Video Research"},
        {"id": "def", "name": "SafeChat"},
    ]

    with patch("tai.core.prompt.inquirer.fuzzy", return_value=_mock_fuzzy("Video Research")):
        result = search_select("Pick:", projects, label_fn=lambda p: p["name"])

    assert result == {"id": "abc", "name": "Video Research"}


def test_search_select_returns_none_on_cancel():
    projects = [{"id": "abc", "name": "Video Research"}]

    with patch("tai.core.prompt.inquirer.fuzzy", return_value=_mock_fuzzy(None)):
        result = search_select("Pick:", projects, label_fn=lambda p: p["name"])

    assert result is None


def test_search_select_returns_none_on_unmatched_input():
    projects = [{"id": "abc", "name": "Video Research"}]

    with patch("tai.core.prompt.inquirer.fuzzy", return_value=_mock_fuzzy("something else")):
        result = search_select("Pick:", projects, label_fn=lambda p: p["name"])

    assert result is None


def test_search_select_passes_max_shown_as_pool_size():
    projects = [{"id": str(i), "name": f"Project {i}"} for i in range(20)]

    captured_choices = None

    def fake_fuzzy(message, choices, **kwargs):
        nonlocal captured_choices
        captured_choices = choices
        return _mock_fuzzy(None)

    with patch("tai.core.prompt.inquirer.fuzzy", side_effect=fake_fuzzy):
        search_select("Pick:", projects, label_fn=lambda p: p["name"], max_shown=5)

    assert len(captured_choices) == 5

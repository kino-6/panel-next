from __future__ import annotations

from pathlib import Path

from panel_next.cli import _resolve_observation_path, _resolve_output_path


def test_default_output_path_uses_timestamp() -> None:
    assert _resolve_output_path(None, "full", "20260530_010203") == Path(
        "outputs/next_panel_20260530_010203.json"
    )


def test_explicit_output_path_wins() -> None:
    assert _resolve_output_path("custom.json", "full", "20260530_010203") == Path(
        "custom.json"
    )


def test_default_observation_path_uses_timestamp_for_full() -> None:
    assert _resolve_observation_path(None, "full", "20260530_010203") == Path(
        "outputs/image_observation_20260530_010203.json"
    )

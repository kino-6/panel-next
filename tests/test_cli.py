from __future__ import annotations

from pathlib import Path

import pytest

from panel_next.cli import (
    _resolve_default_comfyui_dir,
    _resolve_observation_path,
    _resolve_output_dir,
    _resolve_output_path,
)


def test_default_output_path_uses_timestamp() -> None:
    output_dir = _resolve_output_dir("20260530_010203")
    assert output_dir == Path("outputs/20260530_010203")
    assert _resolve_output_path(None, "full", output_dir) == Path(
        "outputs/20260530_010203/next_panel.json"
    )


def test_explicit_output_path_wins() -> None:
    assert _resolve_output_path("custom.json", "full", Path("outputs/run")) == Path(
        "custom.json"
    )


def test_default_observation_path_uses_timestamp_for_full() -> None:
    assert _resolve_observation_path(None, "full", Path("outputs/20260530_010203")) == Path(
        "outputs/20260530_010203/image_observation.json"
    )


def test_plan_mode_requires_explicit_observation_path() -> None:
    with pytest.raises(ValueError, match="--observation is required"):
        _resolve_observation_path(None, "plan", Path("outputs/20260530_010203"))


def test_default_comfyui_dir_uses_run_directory() -> None:
    assert _resolve_default_comfyui_dir("full", Path("outputs/20260530_010203")) == Path(
        "outputs/20260530_010203/comfyui_prompts"
    )
    assert _resolve_default_comfyui_dir("observe", Path("outputs/20260530_010203")) is None

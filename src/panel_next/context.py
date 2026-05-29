from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import ContinuityControl, validate_continuity_control


def build_continuity_control(
    character_concept: str = "",
    background_concept: str = "",
    fixed_elements: list[str] | None = None,
    allowed_changes: list[str] | None = None,
    forbidden_changes: list[str] | None = None,
    context_file: str | Path | None = None,
) -> ContinuityControl:
    data: dict[str, Any] = {
        "character_concept": "",
        "background_concept": "",
        "fixed_elements": [],
        "allowed_changes": [],
        "forbidden_changes": [],
    }
    if context_file:
        data.update(_read_context_file(Path(context_file)))

    if character_concept:
        data["character_concept"] = character_concept
    if background_concept:
        data["background_concept"] = background_concept
    data["fixed_elements"] = _merge_list(data.get("fixed_elements"), fixed_elements)
    data["allowed_changes"] = _merge_list(data.get("allowed_changes"), allowed_changes)
    data["forbidden_changes"] = _merge_list(
        data.get("forbidden_changes"), forbidden_changes
    )
    return validate_continuity_control(data)


def _read_context_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Context file does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Context file is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Context file must contain a JSON object: {path}")
    return data


def _merge_list(base: Any, extra: list[str] | None) -> list[str]:
    values: list[str] = []
    if isinstance(base, str):
        values.append(base)
    elif isinstance(base, list):
        values.extend(str(item) for item in base if str(item).strip())
    elif base:
        values.append(str(base))

    if extra:
        values.extend(item for item in extra if item.strip())
    return values

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import validate_panel_next_output


class ComfyUIExportError(ValueError):
    """Raised when a ComfyUI workflow cannot be exported from a panel plan."""


@dataclass(frozen=True)
class ComfyUIExportConfig:
    plan: Path
    template: Path
    out: Path
    candidate: int
    positive_node: str
    negative_node: str


def export_comfyui_workflow(config: ComfyUIExportConfig) -> dict[str, Any]:
    plan = validate_panel_next_output(_read_json(config.plan, "plan"))
    template = _read_json(config.template, "ComfyUI workflow template")
    if not isinstance(template, dict):
        raise ComfyUIExportError("ComfyUI workflow template must be a JSON object.")

    panel = _select_candidate(plan["next_panels"], config.candidate)
    workflow = json.loads(json.dumps(template, ensure_ascii=False))
    _patch_text_node(
        workflow,
        config.positive_node,
        panel["comfyui_prompt"],
        "positive",
    )
    _patch_text_node(
        workflow,
        config.negative_node,
        panel["negative_prompt"],
        "negative",
    )
    _write_json(config.out, workflow)
    return workflow


def _select_candidate(panels: list[dict[str, Any]], candidate: int) -> dict[str, Any]:
    for panel in panels:
        if int(panel.get("panel_id", -1)) == candidate:
            return panel
    if 1 <= candidate <= len(panels):
        return panels[candidate - 1]
    available = ", ".join(str(panel.get("panel_id", index + 1)) for index, panel in enumerate(panels))
    raise ComfyUIExportError(
        f"Candidate {candidate} was not found. Available candidates: {available}"
    )


def _patch_text_node(
    workflow: dict[str, Any],
    node_id: str,
    text: str,
    label: str,
) -> None:
    if node_id not in workflow:
        raise ComfyUIExportError(f"{label} node id does not exist in template: {node_id}")
    node = workflow[node_id]
    if not isinstance(node, dict):
        raise ComfyUIExportError(f"{label} node {node_id} must be a JSON object.")
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        raise ComfyUIExportError(f"{label} node {node_id} is missing inputs object.")
    if "text" not in inputs:
        raise ComfyUIExportError(f"{label} node {node_id} is missing inputs.text.")
    inputs["text"] = text


def _read_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"{label} file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ComfyUIExportError(f"{label} file is not valid JSON: {path}") from exc


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

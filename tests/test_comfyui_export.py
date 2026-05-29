from __future__ import annotations

import json

import pytest

from panel_next.comfyui_export import (
    ComfyUIExportConfig,
    ComfyUIExportError,
    export_comfyui_workflow,
)


def test_export_comfyui_workflow_patches_prompt_nodes(tmp_path) -> None:
    plan = tmp_path / "plan.json"
    template = tmp_path / "template.json"
    out = tmp_path / "workflow.json"
    plan.write_text(json.dumps(_plan()), encoding="utf-8")
    template.write_text(json.dumps(_workflow()), encoding="utf-8")

    workflow = export_comfyui_workflow(
        ComfyUIExportConfig(
            plan=plan,
            template=template,
            out=out,
            candidate=1,
            positive_node="6",
            negative_node="7",
        )
    )

    assert workflow["6"]["inputs"]["text"] == "positive prompt"
    assert workflow["7"]["inputs"]["text"] == "negative prompt"
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["6"]["inputs"]["text"] == "positive prompt"


def test_export_comfyui_workflow_accepts_utf8_bom_json(tmp_path) -> None:
    plan = tmp_path / "plan.json"
    template = tmp_path / "template.json"
    out = tmp_path / "workflow.json"
    plan.write_text(json.dumps(_plan()), encoding="utf-8-sig")
    template.write_text(json.dumps(_workflow()), encoding="utf-8-sig")

    workflow = export_comfyui_workflow(
        ComfyUIExportConfig(
            plan=plan,
            template=template,
            out=out,
            candidate=1,
            positive_node="6",
            negative_node="7",
        )
    )

    assert workflow["6"]["inputs"]["text"] == "positive prompt"


def test_export_comfyui_workflow_rejects_missing_node(tmp_path) -> None:
    plan = tmp_path / "plan.json"
    template = tmp_path / "template.json"
    out = tmp_path / "workflow.json"
    plan.write_text(json.dumps(_plan()), encoding="utf-8")
    template.write_text(json.dumps(_workflow()), encoding="utf-8")

    with pytest.raises(ComfyUIExportError, match="positive node id"):
        export_comfyui_workflow(
            ComfyUIExportConfig(
                plan=plan,
                template=template,
                out=out,
                candidate=1,
                positive_node="999",
                negative_node="7",
            )
        )


def test_export_comfyui_workflow_rejects_missing_text_input(tmp_path) -> None:
    plan = tmp_path / "plan.json"
    template = tmp_path / "template.json"
    out = tmp_path / "workflow.json"
    workflow = _workflow()
    del workflow["6"]["inputs"]["text"]
    plan.write_text(json.dumps(_plan()), encoding="utf-8")
    template.write_text(json.dumps(workflow), encoding="utf-8")

    with pytest.raises(ComfyUIExportError, match="inputs.text"):
        export_comfyui_workflow(
            ComfyUIExportConfig(
                plan=plan,
                template=template,
                out=out,
                candidate=1,
                positive_node="6",
                negative_node="7",
            )
        )


def _workflow() -> dict:
    return {
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "old positive", "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "old negative", "clip": ["4", 1]},
        },
    }


def _plan() -> dict:
    return {
        "source_image": "data/base.png",
        "user_intent": "look back",
        "image_observation": {
            "summary": "summary",
            "characters": ["1girl"],
            "composition": "medium shot",
            "mood": "quiet",
            "important_visual_details": ["ribbon"],
            "continuity_constraints": [],
        },
        "continuity_control": {
            "character_concept": "",
            "background_concept": "",
            "fixed_elements": [],
            "allowed_changes": [],
            "forbidden_changes": [],
        },
        "next_panels": [
            {
                "panel_id": 1,
                "purpose": "reaction shot",
                "natural_prompt": "positive prompt",
                "prompt_sections": {
                    "fixed": "1girl",
                    "angle": "medium close-up",
                    "screen_effects": "clean linework",
                    "situation": "looking back",
                    "objects": "ribbon",
                },
                "comfyui_prompt": "positive prompt",
                "danbooru_tags": ["1girl"],
                "camera": "medium close-up",
                "emotion": "surprised",
                "continuity_note": "same design",
                "negative_prompt": "negative prompt",
                "why_this_next": "自然につながるため。",
            }
        ],
    }

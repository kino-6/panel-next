from __future__ import annotations

from typing import Any


PROMPT_SECTION_ORDER = ("fixed", "angle", "screen_effects", "situation", "objects")


def ensure_comfyui_prompts(
    panels: Any,
    observation: dict[str, Any],
    continuity_control: dict[str, Any],
) -> Any:
    if not isinstance(panels, list):
        return panels
    for index, panel in enumerate(panels, start=1):
        if not isinstance(panel, dict):
            continue
        ensure_panel_defaults(panel, index, observation, continuity_control)
        sections = panel.get("prompt_sections")
        if not isinstance(sections, dict):
            sections = build_prompt_sections(panel, observation, continuity_control)
            panel["prompt_sections"] = sections
        else:
            fallback = build_prompt_sections(panel, observation, continuity_control)
            for key, value in fallback.items():
                if not isinstance(sections.get(key), str) or not sections[key].strip():
                    sections[key] = value
        if not isinstance(panel.get("comfyui_prompt"), str) or not panel[
            "comfyui_prompt"
        ].strip():
            panel["comfyui_prompt"] = join_prompt_sections(sections)
    return panels


def ensure_panel_defaults(
    panel: dict[str, Any],
    panel_id: int,
    observation: dict[str, Any],
    continuity_control: dict[str, Any],
) -> None:
    panel.setdefault("panel_id", panel_id)
    panel.setdefault("purpose", "next panel candidate")
    panel.setdefault("natural_prompt", str(panel.get("purpose") or "natural next panel beat"))
    panel.setdefault("danbooru_tags", [])
    panel.setdefault(
        "camera",
        str(observation.get("composition") or "natural manga panel framing"),
    )
    panel.setdefault("emotion", "consistent with the intended next beat")
    panel.setdefault(
        "continuity_note",
        "Keep the same character identity, outfit, hairstyle, lighting, and important background elements as the source image.",
    )
    forbidden = [
        str(item)
        for item in continuity_control.get("forbidden_changes", [])
        if str(item).strip()
    ]
    negative_parts = forbidden + [
        "different character",
        "different outfit",
        "extra limbs",
        "distorted hands",
        "low quality",
    ]
    panel.setdefault("negative_prompt", ", ".join(dict.fromkeys(negative_parts)))
    panel.setdefault(
        "why_this_next",
        "前のコマの視覚情報と固定要素を保ちながら、自然な次の変化を作るため。",
    )


def build_prompt_sections(
    panel: dict[str, Any],
    observation: dict[str, Any],
    continuity_control: dict[str, Any],
) -> dict[str, str]:
    fixed_parts = []
    if continuity_control.get("character_concept"):
        fixed_parts.append(str(continuity_control["character_concept"]))
    if continuity_control.get("background_concept"):
        fixed_parts.append(str(continuity_control["background_concept"]))
    fixed_parts.extend(str(item) for item in continuity_control.get("fixed_elements", []))
    fixed_parts.extend(str(item) for item in observation.get("continuity_constraints", []))
    if not fixed_parts:
        fixed_parts.append("same character identity, same outfit, continuity from source image")

    objects = [str(item) for item in observation.get("important_visual_details", [])]
    if observation.get("composition"):
        objects.append(str(observation["composition"]))

    return {
        "fixed": ", ".join(fixed_parts),
        "angle": str(
            panel.get("camera")
            or observation.get("composition")
            or "natural manga panel framing"
        ),
        "screen_effects": "clean anime linework, consistent lighting, polished image quality",
        "situation": str(
            panel.get("natural_prompt") or panel.get("purpose") or "natural next panel beat"
        ),
        "objects": (
            ", ".join(objects) if objects else "preserve visible props and background elements"
        ),
    }


def join_prompt_sections(sections: dict[str, str]) -> str:
    return "\n".join(
        sections[key].strip()
        for key in PROMPT_SECTION_ORDER
        if isinstance(sections.get(key), str) and sections[key].strip()
    )

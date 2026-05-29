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
    for panel in panels:
        if not isinstance(panel, dict):
            continue
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

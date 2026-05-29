from __future__ import annotations

from pathlib import Path
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


def write_comfyui_prompt_files(
    output_dir: Path,
    panels: list[dict[str, Any]],
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, panel in enumerate(panels, start=1):
        panel_id = int(panel.get("panel_id") or index)
        prefix = f"candidate_{panel_id:02d}"
        positive_path = output_dir / f"{prefix}_positive.txt"
        negative_path = output_dir / f"{prefix}_negative.txt"
        sections_path = output_dir / f"{prefix}_sections.txt"

        _write_windows_text(positive_path, str(panel.get("comfyui_prompt", "")))
        _write_windows_text(negative_path, str(panel.get("negative_prompt", "")))
        _write_windows_text(
            sections_path,
            _format_sections(panel.get("prompt_sections", {})),
        )
        written.extend([positive_path, negative_path, sections_path])
    return written


def _format_sections(sections: Any) -> str:
    if not isinstance(sections, dict):
        return ""
    lines = []
    for key in PROMPT_SECTION_ORDER:
        value = sections.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(f"[{key}]")
            lines.append(value.strip())
            lines.append("")
    return "\n".join(lines).strip()


def _write_windows_text(path: Path, text: str) -> None:
    normalized = "\r\n".join(text.splitlines()).strip()
    if normalized:
        normalized += "\r\n"
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(normalized)

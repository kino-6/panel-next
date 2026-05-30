from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .tag_lexicon import BUILTIN_TAG_FREQUENCIES, continuity_text_to_tags


PROMPT_SECTION_ORDER = ("fixed", "angle", "screen_effects", "situation", "objects")


def ensure_comfyui_prompts(
    panels: Any,
    observation: dict[str, Any],
    continuity_control: dict[str, Any],
    tag_frequencies: dict[str, int] | None = None,
) -> Any:
    frequencies = tag_frequencies or BUILTIN_TAG_FREQUENCIES
    if not isinstance(panels, list):
        return panels
    for index, panel in enumerate(panels, start=1):
        if not isinstance(panel, dict):
            continue
        ensure_panel_defaults(panel, index, observation, continuity_control)
        forbidden_terms = _forbidden_terms(continuity_control)
        sections = panel.get("prompt_sections")
        if not isinstance(sections, dict):
            sections = build_prompt_sections(
                panel, observation, continuity_control, frequencies
            )
            panel["prompt_sections"] = sections
        else:
            fallback = build_prompt_sections(
                panel, observation, continuity_control, frequencies
            )
            for key, value in fallback.items():
                if not isinstance(sections.get(key), str) or not sections[key].strip():
                    sections[key] = value
            sections["fixed"] = fallback["fixed"]
        if forbidden_terms:
            sections = _remove_forbidden_from_sections(sections, forbidden_terms)
            panel["prompt_sections"] = sections
        if (
            not isinstance(panel.get("comfyui_prompt"), str)
            or not panel["comfyui_prompt"].strip()
            or _contains_generic_continuity(panel["comfyui_prompt"])
            or forbidden_terms
        ):
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
    panel["negative_prompt"] = _merge_negative_prompt(
        str(panel.get("negative_prompt", "")),
        forbidden,
    )
    panel.setdefault(
        "why_this_next",
        "前のコマの視覚情報と固定要素を保ちながら、自然な次の変化を作るため。",
    )


def build_prompt_sections(
    panel: dict[str, Any],
    observation: dict[str, Any],
    continuity_control: dict[str, Any],
    tag_frequencies: dict[str, int] | None = None,
) -> dict[str, str]:
    fixed_parts: list[str] = []
    if continuity_control.get("character_concept"):
        fixed_parts.append(str(continuity_control["character_concept"]))
    if continuity_control.get("background_concept"):
        fixed_parts.append(str(continuity_control["background_concept"]))
    fixed_parts.extend(str(item) for item in continuity_control.get("fixed_elements", []))
    fixed_parts.extend(str(item) for item in observation.get("continuity_constraints", []))
    if _requests_same_character(continuity_control):
        fixed_parts.extend(_stringify_observation_list(observation.get("characters", [])))
        fixed_parts.extend(str(item) for item in observation.get("important_visual_details", []))

    fixed_text = continuity_text_to_tags(
        fixed_parts + [str(item) for item in observation.get("important_visual_details", [])],
        explicit_tags=panel.get("danbooru_tags", []),
        frequencies=tag_frequencies,
    )

    objects = [str(item) for item in observation.get("important_visual_details", [])]
    if observation.get("composition"):
        objects.append(str(observation["composition"]))

    return {
        "fixed": fixed_text,
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


def _contains_generic_continuity(prompt: str) -> bool:
    lowered = prompt.lower()
    return "same character" in lowered or "continuity from source image" in lowered


def _forbidden_terms(continuity_control: dict[str, Any]) -> list[str]:
    return [
        str(item).strip()
        for item in continuity_control.get("forbidden_changes", [])
        if str(item).strip()
    ]


def _remove_forbidden_from_sections(
    sections: dict[str, Any],
    forbidden_terms: list[str],
) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key in PROMPT_SECTION_ORDER:
        cleaned[key] = _remove_forbidden_terms(str(sections.get(key, "")), forbidden_terms)
    return cleaned


def _remove_forbidden_terms(text: str, forbidden_terms: list[str]) -> str:
    lines = []
    for line in text.splitlines() or [text]:
        cleaned = _remove_forbidden_from_line(line, forbidden_terms)
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip()


def _remove_forbidden_from_line(line: str, forbidden_terms: list[str]) -> str:
    if "," in line:
        parts = [part.strip() for part in line.split(",")]
        kept = [
            part
            for part in parts
            if part and not _contains_forbidden_term(part, forbidden_terms)
        ]
        return ", ".join(kept)

    cleaned = line
    for term in forbidden_terms:
        for form in _term_forms(term):
            cleaned = re.sub(
                rf"(?i)(?<![\w]){re.escape(form)}(?![\w])",
                "",
                cleaned,
            )
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip(" ,.;:")


def _contains_forbidden_term(text: str, forbidden_terms: list[str]) -> bool:
    normalized = _normalize_for_match(text)
    return any(_normalize_for_match(term) in normalized for term in forbidden_terms)


def _term_forms(term: str) -> set[str]:
    stripped = term.strip()
    return {
        stripped,
        stripped.replace(" ", "_"),
        stripped.replace("_", " "),
        stripped.replace("-", "_"),
        stripped.replace("_", "-"),
    }


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[\s-]+", "_", text.strip().lower())


def _merge_negative_prompt(current: str, forbidden_terms: list[str]) -> str:
    parts = [part.strip() for part in current.split(",") if part.strip()]
    parts.extend(forbidden_terms)
    return ", ".join(dict.fromkeys(parts))


def _requests_same_character(continuity_control: dict[str, Any]) -> bool:
    fixed_elements = continuity_control.get("fixed_elements", [])
    haystack = " ".join(str(item) for item in fixed_elements).lower()
    return "same character" in haystack or "character identity" in haystack


def _stringify_observation_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    texts = []
    for item in value:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            texts.extend(str(part) for part in item.values())
        else:
            texts.append(str(item))
    return texts


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

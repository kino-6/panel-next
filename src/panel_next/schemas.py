from __future__ import annotations

import json
import re
from typing import Any, TypedDict


class ImageObservation(TypedDict):
    summary: str
    characters: list[str]
    composition: str
    mood: str
    important_visual_details: list[str]
    continuity_constraints: list[str]


class ContinuityControl(TypedDict):
    character_concept: str
    background_concept: str
    fixed_elements: list[str]
    allowed_changes: list[str]
    forbidden_changes: list[str]


class PromptSections(TypedDict):
    fixed: str
    angle: str
    screen_effects: str
    situation: str
    objects: str


class NextPanel(TypedDict):
    panel_id: int
    purpose: str
    natural_prompt: str
    prompt_sections: PromptSections
    comfyui_prompt: str
    danbooru_tags: list[str]
    camera: str
    emotion: str
    continuity_note: str
    negative_prompt: str
    why_this_next: str


class PanelNextOutput(TypedDict):
    source_image: str
    user_intent: str
    image_observation: ImageObservation
    continuity_control: ContinuityControl
    next_panels: list[NextPanel]


class SchemaValidationError(ValueError):
    """Raised when LLM JSON does not match the minimum required schema."""


IMAGE_OBSERVATION_REQUIRED_KEYS = {
    "summary",
    "characters",
    "composition",
    "mood",
    "important_visual_details",
}
IMAGE_OBSERVATION_TEXT_FIELDS = ("summary", "composition", "mood")
IMAGE_OBSERVATION_LIST_FIELDS = (
    "characters",
    "important_visual_details",
    "continuity_constraints",
)


def extract_json_from_response(response: str) -> Any:
    text = response.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start_candidates = [idx for idx in (text.find("{"), text.find("[")) if idx != -1]
        if not start_candidates:
            raise
        start = min(start_candidates)
        opener = text[start]
        closer = "}" if opener == "{" else "]"
        end = text.rfind(closer)
        if end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def require_keys(data: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - set(data))
    if missing:
        raise SchemaValidationError(f"{label} is missing required keys: {', '.join(missing)}")


def validate_image_observation(data: Any) -> ImageObservation:
    if not isinstance(data, dict):
        raise SchemaValidationError("image_observation must be a JSON object.")
    observation = dict(data)
    require_keys(
        observation,
        IMAGE_OBSERVATION_REQUIRED_KEYS,
        "image_observation",
    )
    observation.setdefault("continuity_constraints", [])
    for key in IMAGE_OBSERVATION_TEXT_FIELDS:
        observation[key] = str(observation.get(key, "")).strip()
    for key in IMAGE_OBSERVATION_LIST_FIELDS:
        observation[key] = _normalize_text_list(
            observation[key],
            f"image_observation.{key}",
        )
    return observation


def validate_next_panel(data: Any) -> NextPanel:
    if not isinstance(data, dict):
        raise SchemaValidationError("Each next panel must be a JSON object.")
    require_keys(
        data,
        {
            "panel_id",
            "purpose",
            "natural_prompt",
            "prompt_sections",
            "comfyui_prompt",
            "danbooru_tags",
            "camera",
            "emotion",
            "continuity_note",
            "negative_prompt",
            "why_this_next",
        },
        "next panel",
    )
    if not isinstance(data["danbooru_tags"], list):
        raise SchemaValidationError("next panel danbooru_tags must be a list.")
    data["prompt_sections"] = validate_prompt_sections(data["prompt_sections"])
    if not isinstance(data["comfyui_prompt"], str) or not data["comfyui_prompt"].strip():
        raise SchemaValidationError("next panel comfyui_prompt must be a non-empty string.")
    return data


def validate_prompt_sections(data: Any) -> PromptSections:
    if not isinstance(data, dict):
        raise SchemaValidationError("next panel prompt_sections must be a JSON object.")
    require_keys(
        data,
        {"fixed", "angle", "screen_effects", "situation", "objects"},
        "prompt_sections",
    )
    for key in ("fixed", "angle", "screen_effects", "situation", "objects"):
        if not isinstance(data[key], str):
            raise SchemaValidationError(f"prompt_sections.{key} must be a string.")
    return data


def validate_continuity_control(data: Any) -> ContinuityControl:
    if not isinstance(data, dict):
        raise SchemaValidationError("continuity_control must be a JSON object.")
    data.setdefault("character_concept", "")
    data.setdefault("background_concept", "")
    data.setdefault("fixed_elements", [])
    data.setdefault("allowed_changes", [])
    data.setdefault("forbidden_changes", [])
    for key in ("fixed_elements", "allowed_changes", "forbidden_changes"):
        if isinstance(data[key], str):
            data[key] = [data[key]]
        if not isinstance(data[key], list):
            raise SchemaValidationError(f"continuity_control.{key} must be a list.")
    return data


def _normalize_text_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str | dict):
        text = _normalize_text_item(value)
        return [text] if text else []
    if isinstance(value, list):
        return [
            text
            for item in value
            if (text := _normalize_text_item(item))
        ]
    raise SchemaValidationError(f"{label} must be a list or text.")


def _normalize_text_item(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return _stringify_jsonish(value)
    return str(value).strip()


def _stringify_jsonish(value: dict[str, Any]) -> str:
    parts = []
    for item in value.values():
        if item is None:
            continue
        if isinstance(item, list):
            parts.extend(str(part).strip() for part in item if str(part).strip())
        elif isinstance(item, dict):
            text = _stringify_jsonish(item)
            if text:
                parts.append(text)
        else:
            text = str(item).strip()
            if text:
                parts.append(text)
    return ", ".join(parts)


def validate_panel_next_output(data: Any) -> PanelNextOutput:
    if not isinstance(data, dict):
        raise SchemaValidationError("Output must be a JSON object.")
    require_keys(
        data,
        {
            "source_image",
            "user_intent",
            "image_observation",
            "continuity_control",
            "next_panels",
        },
        "output",
    )
    data["image_observation"] = validate_image_observation(data["image_observation"])
    data["continuity_control"] = validate_continuity_control(
        data["continuity_control"]
    )
    if not isinstance(data["next_panels"], list) or not data["next_panels"]:
        raise SchemaValidationError("output.next_panels must be a non-empty list.")
    data["next_panels"] = [validate_next_panel(panel) for panel in data["next_panels"]]
    return data

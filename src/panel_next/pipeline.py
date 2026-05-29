from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .image_io import encode_image_base64, validate_image_path
from .ollama_client import OllamaClient
from .prompt_formatting import ensure_comfyui_prompts
from .prompts import build_next_panel_messages, build_vision_messages
from .schemas import (
    ContinuityControl,
    PanelNextOutput,
    extract_json_from_response,
    validate_continuity_control,
    validate_image_observation,
    validate_panel_next_output,
)


DEBUG_RESPONSE_PATH = Path("outputs/debug_last_response.txt")


@dataclass(frozen=True)
class PipelineConfig:
    image: Path
    intent: str
    out: Path
    observation: Path
    vision_model: str
    text_model: str
    ollama_url: str
    candidates: int
    continuity_control: ContinuityControl
    debug: bool = False


def run_observe(config: PipelineConfig, client: OllamaClient | None = None) -> dict[str, Any]:
    validate_image_path(config.image)
    ollama = client or OllamaClient(config.ollama_url)
    image_base64 = encode_image_base64(config.image)
    raw_response = ollama.vision_chat(
        model=config.vision_model,
        messages=build_vision_messages(),
        image_base64=image_base64,
    )
    observation = _parse_or_save_debug(raw_response, "image observation")
    validated = validate_image_observation(observation)
    _write_json(config.observation, validated)
    return validated


def run_plan(
    config: PipelineConfig,
    image_observation: dict[str, Any] | None = None,
    client: OllamaClient | None = None,
) -> PanelNextOutput:
    if image_observation is None:
        image_observation = _read_json(config.observation)
    observation = validate_image_observation(image_observation)
    ollama = client or OllamaClient(config.ollama_url)
    raw_response = ollama.chat(
        model=config.text_model,
        messages=build_next_panel_messages(
            image_observation=observation,
            user_intent=config.intent,
            candidates=config.candidates,
            continuity_control=config.continuity_control,
        ),
    )
    parsed = _parse_or_save_debug(raw_response, "next panel plan")
    panels = parsed.get("next_panels") if isinstance(parsed, dict) else parsed
    panels = ensure_comfyui_prompts(panels, observation, config.continuity_control)
    output: PanelNextOutput = {
        "source_image": str(config.image),
        "user_intent": config.intent,
        "image_observation": observation,
        "continuity_control": validate_continuity_control(config.continuity_control),
        "next_panels": panels,
    }
    validated = validate_panel_next_output(output)
    _write_json(config.out, validated)
    return validated


def run_full(config: PipelineConfig, client: OllamaClient | None = None) -> PanelNextOutput:
    ollama = client or OllamaClient(config.ollama_url)
    observation = run_observe(config, client=ollama)
    return run_plan(config, image_observation=observation, client=ollama)


def print_summary(output: PanelNextOutput | dict[str, Any], mode: str) -> None:
    if mode == "observe":
        print("Image observation saved.")
        print(f"Summary: {output.get('summary', '')}")
        return

    panels = output.get("next_panels", [])
    print(f"Saved {len(panels)} next panel candidate(s).")
    for panel in panels:
        panel_id = panel.get("panel_id", "?")
        purpose = panel.get("purpose", "")
        camera = panel.get("camera", "")
        print(f"- #{panel_id}: {purpose} / {camera}")


def _parse_or_save_debug(raw_response: str, label: str) -> Any:
    try:
        return extract_json_from_response(raw_response)
    except json.JSONDecodeError as exc:
        DEBUG_RESPONSE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_RESPONSE_PATH.write_text(raw_response, encoding="utf-8")
        raise ValueError(
            f"Failed to parse {label} JSON from LLM response. "
            f"Raw response was saved to {DEBUG_RESPONSE_PATH}."
        ) from exc


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(
            f"Observation JSON does not exist: {path}. "
            "Run --mode observe or --mode full first, or pass --observation."
        )
    return json.loads(path.read_text(encoding="utf-8"))

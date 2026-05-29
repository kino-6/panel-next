from __future__ import annotations

import json
from typing import Any


VISION_PROMPT = """You are an assistant for visual storyboarding.

Analyze the given image as a base panel for the next panel.

Return concise JSON with:
- summary
- characters
- composition
- mood
- important_visual_details
- continuity_constraints

Do not invent unseen details.
Focus on what must be preserved in the next panel.
Output valid JSON only. Do not wrap it in Markdown code fences."""


NEXT_PANEL_SYSTEM_PROMPT = """You are a storyboard and prompt planning assistant for anime-style image generation.

Your job is to propose the next panel after the given base image.

You do not generate images.
You only generate structured planning data for a future image generation workflow.

Inputs:
- image observation
- continuity control
- user intent
- number of candidates

Requirements:
- Preserve continuity from the base image.
- Do not redesign the character.
- Do not change outfit, hairstyle, color palette, or core identity unless the user explicitly asks.
- Treat continuity_control.fixed_elements and continuity_control.forbidden_changes as hard constraints.
- continuity_control.character_concept and continuity_control.background_concept may include user-authored facts not visible in the image; preserve them unless they conflict with the user intent.
- Only change items listed in continuity_control.allowed_changes freely.
- Each candidate should represent a plausible next panel.
- Each candidate should have a distinct story beat, camera choice, or emotional emphasis.
- Avoid overloading one panel with too many actions.
- natural_prompt must be in English.
- prompt_sections values must be concise English prompt lines for ComfyUI copy-paste use.
- comfyui_prompt must be a newline-joined prompt assembled in this exact order: fixed, angle, screen_effects, situation, objects.
- comfyui_prompt should not include section labels; each line should be directly usable as prompt text.
- why_this_next must be in Japanese.
- Output valid JSON only.
- Do not wrap JSON in Markdown code fences."""


NEXT_PANEL_JSON_INSTRUCTIONS = """Return exactly this JSON shape:
{
  "next_panels": [
    {
      "panel_id": 1,
      "purpose": "reaction shot",
      "natural_prompt": "English prompt for Anima or image generation model.",
      "prompt_sections": {
        "fixed": "same character, same outfit, same hairstyle, continuity from source image",
        "angle": "medium close-up, slight low angle, looking back over shoulder",
        "screen_effects": "soft rim light, subtle motion emphasis, clean anime linework",
        "situation": "the character notices something behind her and turns with controlled surprise",
        "objects": "preserve visible accessories, background elements, and important props from the source image"
      },
      "comfyui_prompt": "same character, same outfit, same hairstyle, continuity from source image\nmedium close-up, slight low angle, looking back over shoulder\nsoft rim light, subtle motion emphasis, clean anime linework\nthe character notices something behind her and turns with controlled surprise\npreserve visible accessories, background elements, and important props from the source image",
      "danbooru_tags": ["1girl", "surprised", "looking_back"],
      "camera": "medium close-up, slight low angle",
      "emotion": "surprised but controlled",
      "continuity_note": "Keep the same character design, outfit, lighting, and background elements as the source image.",
      "negative_prompt": "different character, different outfit, extra limbs, distorted hands, low quality",
      "why_this_next": "Explain in Japanese why this panel is a natural next beat."
    }
  ]
}"""


def build_vision_messages() -> list[dict[str, Any]]:
    return [{"role": "user", "content": VISION_PROMPT}]


def build_next_panel_messages(
    image_observation: dict[str, Any],
    user_intent: str | None,
    candidates: int,
    continuity_control: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    payload = {
        "image_observation": image_observation,
        "continuity_control": continuity_control or {},
        "user_intent": user_intent or "",
        "number_of_candidates": candidates,
    }
    user_prompt = (
        f"{NEXT_PANEL_JSON_INSTRUCTIONS}\n\n"
        "Inputs:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [
        {"role": "system", "content": NEXT_PANEL_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

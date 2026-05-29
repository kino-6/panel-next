from __future__ import annotations

import pytest

from panel_next.image_io import ImageInputError, validate_image_path
from panel_next.schemas import extract_json_from_response, validate_panel_next_output


def test_output_schema_validation_accepts_minimum_shape() -> None:
    data = {
        "source_image": "examples/base.png",
        "user_intent": "Give me three natural next-panel candidates.",
        "image_observation": {
            "summary": "A character stands in a room.",
            "characters": ["1girl"],
            "composition": "medium shot",
            "mood": "quiet",
            "important_visual_details": ["same outfit"],
            "continuity_constraints": ["same lighting"],
        },
        "continuity_control": {
            "character_concept": "A quiet girl with a red ribbon.",
            "background_concept": "Rainy shrine at night.",
            "fixed_elements": ["red ribbon", "same outfit"],
            "allowed_changes": ["expression", "pose"],
            "forbidden_changes": ["different character"],
        },
        "next_panels": [
            {
                "panel_id": 1,
                "purpose": "reaction shot",
                "natural_prompt": "Anime girl looking back with a surprised expression.",
                "prompt_sections": {
                    "fixed": "same girl, red ribbon, same outfit",
                    "angle": "medium close-up, looking back",
                    "screen_effects": "soft rain glow, clean anime linework",
                    "situation": "she notices something behind her",
                    "objects": "wet shrine stones, torii gate, red ribbon",
                },
                "comfyui_prompt": (
                    "same girl, red ribbon, same outfit\n"
                    "medium close-up, looking back\n"
                    "soft rain glow, clean anime linework\n"
                    "she notices something behind her\n"
                    "wet shrine stones, torii gate, red ribbon"
                ),
                "danbooru_tags": ["1girl", "surprised", "looking_back"],
                "camera": "medium close-up",
                "emotion": "surprised but controlled",
                "continuity_note": "Keep the same character design.",
                "negative_prompt": "different character, low quality",
                "why_this_next": "The gaze shift creates a natural next beat.",
            }
        ],
    }

    panel = validate_panel_next_output(data)["next_panels"][0]
    assert panel["panel_id"] == 1
    assert "medium close-up" in panel["comfyui_prompt"]


def test_missing_image_path_raises_error(tmp_path) -> None:
    missing = tmp_path / "missing.png"

    with pytest.raises(ImageInputError):
        validate_image_path(missing)


def test_extract_json_from_markdown_code_block() -> None:
    response = """```json
{"next_panels": [{"panel_id": 1}]}
```"""

    assert extract_json_from_response(response) == {"next_panels": [{"panel_id": 1}]}

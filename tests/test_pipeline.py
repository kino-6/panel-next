from __future__ import annotations

from panel_next.prompt_formatting import ensure_comfyui_prompts


def test_ensure_comfyui_prompts_fills_missing_fields() -> None:
    panels = [
        {
            "panel_id": 1,
            "purpose": "reaction shot",
            "natural_prompt": "same bunny girl looks back with a controlled surprise",
            "camera": "medium close-up",
        }
    ]
    observation = {
        "composition": "back view",
        "important_visual_details": ["blue ribbon", "white jacket"],
        "continuity_constraints": ["same outfit"],
    }
    continuity_control = {
        "character_concept": "same bunny girl",
        "background_concept": "plain white background",
        "fixed_elements": ["light blue bunny ears"],
    }

    result = ensure_comfyui_prompts(panels, observation, continuity_control)

    panel = result[0]
    assert panel["prompt_sections"]["fixed"].startswith("same bunny girl")
    assert panel["prompt_sections"]["angle"] == "medium close-up"
    assert "blue ribbon" in panel["prompt_sections"]["objects"]
    assert "\n" in panel["comfyui_prompt"]

from __future__ import annotations

from panel_next.prompt_formatting import ensure_comfyui_prompts, write_comfyui_prompt_files


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
    assert panel["continuity_note"].startswith("Keep the same character identity")
    assert "different character" in panel["negative_prompt"]
    assert "bunny_ears" in panel["prompt_sections"]["fixed"]
    assert "same character" not in panel["prompt_sections"]["fixed"]
    assert panel["prompt_sections"]["angle"] == "medium close-up"
    assert "blue ribbon" in panel["prompt_sections"]["objects"]
    assert "\n" in panel["comfyui_prompt"]


def test_ensure_comfyui_prompts_rewrites_generic_fixed_prompt() -> None:
    panels = [
        {
            "panel_id": 1,
            "purpose": "reaction shot",
            "natural_prompt": "blonde bunny girl looking back",
            "prompt_sections": {
                "fixed": "same character, same outfit, same hairstyle",
                "angle": "medium close-up",
                "screen_effects": "clean linework",
                "situation": "looking back",
                "objects": "blue ribbon",
            },
            "comfyui_prompt": "same character, same outfit, same hairstyle\nmedium close-up",
            "danbooru_tags": ["1girl", "looking_back"],
        }
    ]
    observation = {
        "composition": "back view",
        "important_visual_details": ["blonde hair", "bunny ears", "blue ribbon"],
        "continuity_constraints": ["same outfit"],
    }

    result = ensure_comfyui_prompts(panels, observation, {})

    fixed = result[0]["prompt_sections"]["fixed"]
    assert "blonde_hair" in fixed
    assert "bunny_ears" in fixed
    assert "same character" not in result[0]["comfyui_prompt"]


def test_same_character_fixed_uses_observed_character_details() -> None:
    panels = [
        {
            "panel_id": 1,
            "purpose": "reaction shot",
            "natural_prompt": "looking back",
            "camera": "medium close-up",
            "danbooru_tags": ["1girl"],
        }
    ]
    observation = {
        "characters": [
            {
                "name": "Bunny girl",
                "traits": [
                    "blonde long hair",
                    "blue bunny ears",
                    "pink eyes",
                    "blue ribbon",
                ],
            }
        ],
        "composition": "back view",
        "important_visual_details": [],
        "continuity_constraints": [],
    }
    continuity_control = {"fixed_elements": ["same character"]}

    result = ensure_comfyui_prompts(panels, observation, continuity_control)

    fixed = result[0]["prompt_sections"]["fixed"]
    assert "1girl" in fixed
    assert "blonde_hair" in fixed
    assert "bunny_ears" in fixed
    assert "same character" not in fixed


def test_write_comfyui_prompt_files_uses_windows_line_endings(tmp_path) -> None:
    panels = [
        {
            "panel_id": 1,
            "purpose": "reaction shot",
            "comfyui_prompt": "fixed line\nangle line",
            "negative_prompt": "different character, low quality",
            "prompt_sections": {
                "fixed": "fixed line",
                "angle": "angle line",
                "screen_effects": "effect line",
                "situation": "situation line",
                "objects": "object line",
            },
        }
    ]

    written = write_comfyui_prompt_files(tmp_path, panels)

    assert tmp_path.joinpath("candidate_01_positive.txt").read_bytes() == (
        b"fixed line\r\nangle line\r\n"
    )
    assert tmp_path.joinpath("candidate_01_negative.txt").read_text(
        encoding="utf-8"
    ) == "different character, low quality\n"
    assert tmp_path.joinpath("candidate_01_sections.txt") in written

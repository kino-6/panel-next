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
    assert panel["prompt_sections"]["fixed"].startswith("same bunny girl")
    assert panel["prompt_sections"]["angle"] == "medium close-up"
    assert "blue ribbon" in panel["prompt_sections"]["objects"]
    assert "\n" in panel["comfyui_prompt"]


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

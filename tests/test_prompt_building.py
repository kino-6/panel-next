from __future__ import annotations

from panel_next.prompts import NEXT_PANEL_SYSTEM_PROMPT, VISION_PROMPT, build_next_panel_messages


def test_vision_prompt_contains_required_constraints() -> None:
    assert "Do not invent unseen details" in VISION_PROMPT
    assert "continuity_constraints" in VISION_PROMPT
    assert "Output valid JSON only" in VISION_PROMPT


def test_next_panel_prompt_contains_generation_constraints() -> None:
    assert "You do not generate images" in NEXT_PANEL_SYSTEM_PROMPT
    assert "Do not redesign the character" in NEXT_PANEL_SYSTEM_PROMPT
    assert "continuity_control.fixed_elements" in NEXT_PANEL_SYSTEM_PROMPT
    assert "comfyui_prompt must be a newline-joined prompt" in NEXT_PANEL_SYSTEM_PROMPT
    assert "natural_prompt must be in English" in NEXT_PANEL_SYSTEM_PROMPT
    assert "why_this_next must be in Japanese" in NEXT_PANEL_SYSTEM_PROMPT


def test_next_panel_messages_include_user_inputs_and_prompt_sections() -> None:
    messages = build_next_panel_messages(
        image_observation={
            "summary": "A quiet close-up.",
            "characters": ["1girl"],
            "composition": "close-up",
            "mood": "tense",
            "important_visual_details": ["red ribbon"],
            "continuity_constraints": ["same ribbon"],
        },
        user_intent="look back",
        candidates=3,
        continuity_control={
            "character_concept": "black bob hair girl",
            "background_concept": "rainy shrine",
            "fixed_elements": ["red ribbon"],
            "allowed_changes": ["expression"],
            "forbidden_changes": ["different outfit"],
        },
    )

    prompt = messages[-1]["content"]
    assert "look back" in prompt
    assert "red ribbon" in prompt
    assert "continuity_control" in prompt
    assert "prompt_sections" in prompt
    assert "comfyui_prompt" in prompt
    assert "number_of_candidates" in prompt
    assert "next_panels" in prompt

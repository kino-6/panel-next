from __future__ import annotations

import json

from panel_next.context import build_continuity_control


def test_build_continuity_control_merges_file_and_cli_values(tmp_path) -> None:
    context_file = tmp_path / "context.json"
    context_file.write_text(
        json.dumps(
            {
                "character_concept": "file character",
                "background_concept": "file background",
                "fixed_elements": ["same outfit"],
                "allowed_changes": ["camera angle"],
                "forbidden_changes": ["daytime"],
            }
        ),
        encoding="utf-8",
    )

    control = build_continuity_control(
        character_concept="cli character",
        fixed_elements=["red ribbon"],
        forbidden_changes=["different character"],
        context_file=context_file,
    )

    assert control["character_concept"] == "cli character"
    assert control["background_concept"] == "file background"
    assert control["fixed_elements"] == ["same outfit", "red ribbon"]
    assert control["forbidden_changes"] == ["daytime", "different character"]

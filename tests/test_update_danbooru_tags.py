from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_danbooru_tags.py"
SPEC = importlib.util.spec_from_file_location("update_danbooru_tags", SCRIPT_PATH)
assert SPEC is not None
update_danbooru_tags = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(update_danbooru_tags)


def test_write_danbooru_tag_csv(tmp_path) -> None:
    output = tmp_path / "danbooru_tags.csv"

    update_danbooru_tags.write_csv(
        output,
        [
            {
                "word": "1girl",
                "frequency": 100,
                "category": 0,
                "is_deprecated": False,
            }
        ],
    )

    with output.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {
            "word": "1girl",
            "frequency": "100",
            "category": "0",
            "is_deprecated": "False",
        }
    ]

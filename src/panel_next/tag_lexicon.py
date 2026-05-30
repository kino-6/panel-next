from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


BUILTIN_TAG_FREQUENCIES: dict[str, int] = {
    "1girl": 10_000_000,
    "solo": 9_000_000,
    "long_hair": 7_500_000,
    "blonde_hair": 5_000_000,
    "blue_eyes": 4_000_000,
    "pink_eyes": 900_000,
    "smile": 6_000_000,
    "looking_back": 700_000,
    "looking_at_viewer": 5_500_000,
    "surprised": 1_200_000,
    "head_tilt": 350_000,
    "ribbon": 2_500_000,
    "hair_ribbon": 1_000_000,
    "blue_ribbon": 250_000,
    "bunny_girl": 650_000,
    "bunny_ears": 1_000_000,
    "leotard": 900_000,
    "blue_leotard": 60_000,
    "bodysuit": 550_000,
    "jacket": 2_000_000,
    "fur_trim": 240_000,
    "white_jacket": 180_000,
    "white_background": 800_000,
    "simple_background": 3_500_000,
    "back": 700_000,
    "from_behind": 1_100_000,
    "three-quarter_view": 100_000,
    "close-up": 1_500_000,
    "upper_body": 2_000_000,
    "motion_lines": 550_000,
    "depth_of_field": 800_000,
}


PHRASE_TO_TAGS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("female character", ("1girl",)),
    ("anime girl", ("1girl",)),
    ("girl", ("1girl",)),
    ("bunny girl", ("bunny_girl", "bunny_ears")),
    ("bunny ears", ("bunny_ears",)),
    ("blonde", ("blonde_hair",)),
    ("long hair", ("long_hair",)),
    ("pink eyes", ("pink_eyes",)),
    ("blue eyes", ("blue_eyes",)),
    ("blue ribbon", ("blue_ribbon", "hair_ribbon", "ribbon")),
    ("hair ribbon", ("hair_ribbon", "ribbon")),
    ("ribbon", ("ribbon",)),
    ("light blue bodysuit", ("bodysuit", "blue_leotard")),
    ("blue bodysuit", ("bodysuit", "blue_leotard")),
    ("leotard", ("leotard",)),
    ("jacket", ("jacket",)),
    ("fur-lined", ("fur_trim",)),
    ("fur trim", ("fur_trim",)),
    ("white background", ("white_background", "simple_background")),
    ("plain white background", ("white_background", "simple_background")),
    ("simple background", ("simple_background",)),
    ("back view", ("from_behind", "back")),
    ("from behind", ("from_behind",)),
    ("looking back", ("looking_back",)),
    ("look back", ("looking_back",)),
    ("surprise", ("surprised",)),
    ("surprised", ("surprised",)),
    ("head tilt", ("head_tilt",)),
    ("motion lines", ("motion_lines",)),
    ("depth of field", ("depth_of_field",)),
    ("close-up", ("close-up",)),
    ("medium close-up", ("close-up", "upper_body")),
)


GENERIC_CONTINUITY_PATTERNS = (
    re.compile(r"\bsame\b", re.IGNORECASE),
    re.compile(r"\bcontinuity\b", re.IGNORECASE),
    re.compile(r"\bsource image\b", re.IGNORECASE),
    re.compile(r"\bpreserve\b", re.IGNORECASE),
    re.compile(r"\bkeep\b", re.IGNORECASE),
    re.compile(r"\bcharacter identity\b", re.IGNORECASE),
)


def load_tag_frequencies(path: str | Path | None) -> dict[str, int]:
    frequencies = dict(BUILTIN_TAG_FREQUENCIES)
    if path is None:
        return frequencies

    lexicon_path = Path(path)
    if not lexicon_path.exists():
        raise FileNotFoundError(f"Tag lexicon does not exist: {lexicon_path}")
    if lexicon_path.suffix.lower() == ".json":
        frequencies.update(_read_json_lexicon(lexicon_path))
        return frequencies
    frequencies.update(_read_csv_lexicon(lexicon_path))
    return frequencies


def extract_ranked_tags(
    texts: list[str],
    explicit_tags: list[str] | None = None,
    frequencies: dict[str, int] | None = None,
    limit: int = 18,
    trust_explicit: bool = False,
) -> list[str]:
    tag_frequencies = frequencies or BUILTIN_TAG_FREQUENCIES
    found: set[str] = set()
    haystack = "\n".join(text for text in texts if text).lower()
    for tag in explicit_tags or []:
        normalized = normalize_tag(tag)
        if normalized in tag_frequencies and (
            trust_explicit or _tag_is_supported_by_text(normalized, haystack)
        ):
            found.add(normalized)

    for phrase, tags in PHRASE_TO_TAGS:
        if phrase in haystack:
            found.update(tags)

    for raw in re.findall(r"[A-Za-z0-9][A-Za-z0-9_+-]*", haystack):
        normalized = normalize_tag(raw)
        if normalized in tag_frequencies:
            found.add(normalized)

    return sorted(
        found,
        key=lambda tag: (-tag_frequencies.get(tag, 0), tag),
    )[:limit]


def continuity_text_to_tags(
    texts: list[str],
    explicit_tags: list[str] | None = None,
    frequencies: dict[str, int] | None = None,
    trust_explicit: bool = False,
) -> str:
    tags = extract_ranked_tags(
        texts,
        explicit_tags=explicit_tags,
        frequencies=frequencies,
        trust_explicit=trust_explicit,
    )
    if tags:
        return ", ".join(tags)
    cleaned = [
        text
        for text in texts
        if text and not any(pattern.search(text) for pattern in GENERIC_CONTINUITY_PATTERNS)
    ]
    return ", ".join(cleaned) if cleaned else "high quality, detailed anime illustration"


def normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "_")


def _tag_is_supported_by_text(tag: str, haystack: str) -> bool:
    words = [word for word in tag.replace("-", "_").split("_") if word]
    if not words:
        return False
    return all(word in haystack for word in words)


def _read_json_lexicon(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {normalize_tag(str(key)): int(value) for key, value in data.items()}
    if isinstance(data, list):
        result = {}
        for item in data:
            if isinstance(item, dict):
                word = item.get("word") or item.get("tag") or item.get("name")
                frequency = item.get("frequency") or item.get("count") or 0
                if word:
                    result[normalize_tag(str(word))] = int(frequency)
        return result
    raise ValueError(f"Unsupported JSON tag lexicon shape: {path}")


def _read_csv_lexicon(path: Path) -> dict[str, int]:
    result = {}
    with path.open("r", encoding="utf-8", newline="") as file:
        sample = file.read(2048)
        file.seek(0)
        has_header = csv.Sniffer().has_header(sample)
        if has_header:
            reader = csv.DictReader(file)
            for row in reader:
                word = row.get("word") or row.get("tag") or row.get("name")
                frequency = row.get("frequency") or row.get("count") or "0"
                if word:
                    result[normalize_tag(word)] = int(float(frequency))
        else:
            reader = csv.reader(file)
            for row in reader:
                if not row:
                    continue
                frequency = row[1] if len(row) > 1 else "0"
                result[normalize_tag(row[0])] = int(float(frequency))
    return result

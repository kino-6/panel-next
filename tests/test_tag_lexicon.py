from __future__ import annotations

from panel_next.tag_lexicon import continuity_text_to_tags, load_tag_frequencies


def test_continuity_text_to_tags_prefers_ranked_tags() -> None:
    prompt = continuity_text_to_tags(
        ["same bunny girl character", "blonde hair", "blue ribbon", "plain white background"],
        explicit_tags=["looking_back", "not_a_real_builtin_tag"],
    )

    assert prompt.startswith("1girl")
    assert "blonde_hair" in prompt
    assert "bunny_ears" in prompt
    assert "not_a_real_builtin_tag" not in prompt
    assert "same character" not in prompt


def test_continuity_text_to_tags_does_not_trust_unsupported_explicit_tags() -> None:
    prompt = continuity_text_to_tags(
        ["brown hair", "red bow", "school uniform"],
        explicit_tags=["bodysuit", "looking_back"],
    )

    assert "bodysuit" not in prompt
    assert "looking_back" not in prompt


def test_load_csv_tag_lexicon_overrides_frequencies(tmp_path) -> None:
    lexicon = tmp_path / "tags.csv"
    lexicon.write_text(
        "word,frequency\nbunny_ears,1\nribbon,2\nhair_ribbon,3\nblue_ribbon,999999\n",
        encoding="utf-8",
    )

    frequencies = load_tag_frequencies(lexicon)
    prompt = continuity_text_to_tags(
        ["bunny ears", "blue ribbon"],
        frequencies=frequencies,
    )

    assert prompt.split(", ")[0] == "blue_ribbon"

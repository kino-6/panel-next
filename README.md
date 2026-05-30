# panel-next

`panel-next` is a lightweight Python CLI that asks local Ollama models to plan the next storyboard panel from a base image.

It does not generate images. It produces structured JSON and copy-paste prompts for a later ComfyUI, Anima, or other image generation workflow.

## Quick Start

Python 3.11+ and Ollama are required.

```powershell
uv sync
ollama serve
ollama pull huihui_ai/qwen3-abliterated:8b
ollama pull huihui_ai/qwen3-vl-abliterated:8b
```

Run the default full pipeline:

```powershell
uv run python -m panel_next `
  --image data\base.png `
  --intent "次のコマ候補を考えて" `
  --character "same main character"
```

That is the normal use case. The CLI reads the image, creates a fresh observation, asks the text model for next-panel candidates, prints copy-paste prompts to the terminal, and writes related files under one run directory.

```text
outputs/<timestamp>/
  image_observation.json
  next_panel.json
  comfyui_prompts/
    candidate_01_positive.txt
    candidate_01_negative.txt
    candidate_01_sections.txt
```

PowerShell uses a backtick for line continuation. One-line form is also fine:

```powershell
uv run python -m panel_next --image data\base.png --intent "次のコマ候補を考えて" --character "same main character"
```

## What It Does

1. Reads a base image with an Ollama vision model.
2. Extracts visible characters, composition, mood, and details.
3. Combines that with user intent and optional character notes.
4. Produces next-panel candidates as JSON.
5. Prints ComfyUI-friendly positive and negative prompts.

## Core Options

- `--image`: input image path. Required.
- `--intent`: what you want from the next panel. Example: `次のコマ候補を考えて`.
- `--character`: short character concept or continuity note. Example: `same main character`.

Most runs should only need those three.

## Output

The terminal prints each candidate in a copy-paste format:

```text
=== Candidate 1: reaction shot ===
POSITIVE:
1girl, long_hair, hair_ribbon, school_uniform
medium close-up, slight low angle
soft rim light, clean anime linework
the character notices something and reacts
classroom background, desk, window light
NEGATIVE:
different character, different outfit, extra limbs, distorted hands, low quality
```

The same data is saved in `next_panel.json`:

```json
{
  "source_image": "data/base.png",
  "user_intent": "次のコマ候補を考えて",
  "image_observation": {
    "summary": "...",
    "characters": ["..."],
    "composition": "...",
    "mood": "...",
    "important_visual_details": ["..."],
    "continuity_constraints": ["..."]
  },
  "continuity_control": {
    "character_concept": "same main character",
    "background_concept": "",
    "fixed_elements": [],
    "allowed_changes": [],
    "forbidden_changes": []
  },
  "next_panels": [
    {
      "panel_id": 1,
      "purpose": "reaction shot",
      "comfyui_prompt": "...",
      "negative_prompt": "...",
      "why_this_next": "..."
    }
  ]
}
```

## Advanced CLI

Use these only when you need more control.

```powershell
uv run python -m panel_next `
  --image data\base.png `
  --intent "少し驚いて振り向く次のコマ候補を考えて" `
  --character "17-year-old quiet girl, black bob hair, red ribbon" `
  --background "rainy nighttime shrine" `
  --fixed "same outfit" `
  --fixed "red ribbon" `
  --allowed "facial expression" `
  --allowed "camera angle" `
  --avoid "different character" `
  --candidates 3
```

Important options:

- `--fixed`: element that must be preserved. Can be passed multiple times.
- `--allowed`: element that may change freely. Can be passed multiple times.
- `--avoid`: forbidden change or detail. Can be passed multiple times.
- `--background`: background or setting concept to preserve.
- `--context-file`: JSON file containing continuity controls.
- `--out`: explicit output JSON path. Default: `outputs/<timestamp>/next_panel.json`.
- `--comfyui-dir`: explicit prompt text output directory. Default: `outputs/<timestamp>/comfyui_prompts`.
- `--candidates`: number of next-panel candidates. Default: `3`.
- `--vision-model`: Ollama vision model. Default: `huihui_ai/qwen3-vl-abliterated:8b`.
- `--text-model`: Ollama text model. Default: `huihui_ai/qwen3-abliterated:8b`.
- `--ollama-url`: Ollama API URL. Default: `http://localhost:11434`.
- `--no-print-prompts`: do not print prompt blocks to the terminal.
- `--debug`: print intermediate JSON.

## Modes

Default mode is `full`, which regenerates image observation every run. This avoids accidentally mixing an old observation with a new image.

```powershell
uv run python -m panel_next --image data\base.png --intent "次のコマ候補を考えて"
```

Use `observe` only when you want to inspect image analysis:

```powershell
uv run python -m panel_next `
  --mode observe `
  --image data\base.png
```

Use `plan` only when you intentionally want to reuse a specific observation. `--observation` is required.

```powershell
uv run python -m panel_next `
  --mode plan `
  --image data\base.png `
  --observation outputs\20260530_010122\image_observation.json `
  --intent "次のコマ候補を考えて"
```

## Danbooru Tags

`panel-next` uses `data/danbooru_tags.csv` as a baseline tag frequency lexicon. This helps convert vague continuity notes into concrete tag-like prompt text.

Regenerate the tag snapshot:

```powershell
uv run python scripts\update_danbooru_tags.py `
  --out data\danbooru_tags.csv `
  --min-count 50 `
  --max-pages 200
```

You can also pass another CSV or JSON file:

```powershell
uv run python -m panel_next `
  --image data\base.png `
  --intent "次のコマ候補を考えて" `
  --tag-lexicon data\danbooru_tags.csv
```

## Export ComfyUI Workflow JSON

If you have a ComfyUI API workflow template, `panel-next` can export a candidate into that workflow by replacing the positive and negative prompt nodes.

```powershell
uv run python -m panel_next export-comfyui `
  --plan outputs\20260530_010122\next_panel.json `
  --candidate 1 `
  --template workflows\comfyui_api_template.json `
  --positive-node 6 `
  --negative-node 7 `
  --out outputs\20260530_010122\comfyui_candidate_01.json
```

The template must be ComfyUI's API prompt format: a JSON object keyed by node id. The specified positive and negative nodes must have `inputs.text`. Only those two text fields are changed.

See `workflows/README.md` for the template contract.

## Troubleshooting

- `No module named panel_next`: run through `uv run python -m panel_next ...`, or install with `python -m pip install -e .`.
- `Could not connect to Ollama`: start Ollama with `ollama serve`.
- `model not found`: run `ollama list`, then pass the exact model with `--vision-model` or `--text-model`.
- `--mode plan` requires `--observation`: use default full mode unless you intentionally reuse an observation.
- `Failed to parse ... JSON`: raw LLM output is saved to `outputs/debug_last_response.txt`.
- Unsupported image format: use PNG, JPG, JPEG, or WEBP.

## Tests

```powershell
uv run pytest
```

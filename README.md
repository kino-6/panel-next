# panel-next

`panel-next` is a lightweight Python CLI that asks local Ollama models to plan the next storyboard panel from a base image.

It does not generate images. It produces structured JSON for a later ComfyUI, Anima, or other image generation workflow.

## What It Does

1. Reads a base image with an Ollama vision model.
2. Converts the observation into continuity-focused JSON.
3. Combines auto-detected details with user-authored continuity controls.
4. Asks an Ollama text model to propose next-panel candidates.
5. Saves the result as JSON and prints a short summary.

## Install

Python 3.11+ is required.

```bash
uv sync
```

After `uv sync`, run the CLI through uv:

```bash
uv run python -m panel_next --help
```

If you want to run `python -m panel_next` directly with your current Python, install the package into that Python environment:

```bash
python -m pip install -e .
```

If you see `No module named panel_next`, the package is not installed in the Python interpreter you are using. Use `uv run python -m panel_next ...` or run `python -m pip install -e .` first.

## Start Ollama

Run Ollama locally:

```bash
ollama serve
```

Pull the default models:

```bash
ollama pull huihui_ai/qwen3-abliterated:8b
ollama pull huihui_ai/qwen3-vl-abliterated:8b
```

Vision model names can differ by environment. Check available models with:

```bash
ollama list
```

Then pass the model name explicitly:

```bash
uv run python -m panel_next --image examples/base.png --vision-model your-vl-model:tag
```

## Usage

Full pipeline:

```bash
uv run python -m panel_next \
  --image data/base.png \
  --intent "Make the next panel a natural surprised look-back beat." \
  --fixed "same hairstyle" \
  --fixed "same outfit" \
  --fixed "same important accessories"
```

PowerShell uses a backtick for line continuation, not `\`:

```powershell
uv run python -m panel_next `
  --image data\base.png `
  --intent "Make the next panel a natural surprised look-back beat." `
  --fixed "same hairstyle" `
  --fixed "same outfit" `
  --fixed "same important accessories"
```

You can also run it as a single line:

```powershell
uv run python -m panel_next --image data\base.png --intent "Make the next panel a natural surprised look-back beat." --fixed "same hairstyle" --fixed "same outfit" --fixed "same important accessories"
```

If `--out` is omitted, the CLI writes `outputs/next_panel_<timestamp>.json`. In full mode, the observation is also saved as `outputs/image_observation_<timestamp>.json`.

Example with concrete continuity controls:

```bash
uv run python -m panel_next \
  --image examples/base.png \
  --intent "The character notices something behind her." \
  --character "17-year-old quiet girl, black bob hair, red ribbon, reserved but strong-willed" \
  --background "Rainy nighttime shrine with stone pavement, torii gate, and wet trees" \
  --fixed "same outfit" \
  --fixed "red ribbon" \
  --fixed "rainy nighttime shrine atmosphere" \
  --allowed "facial expression" \
  --allowed "camera angle" \
  --avoid "different character" \
  --avoid "daytime" \
  --candidates 3
```

With explicit models:

```bash
uv run python -m panel_next \
  --image examples/base.png \
  --intent "Give me three natural next-panel candidates." \
  --vision-model huihui_ai/qwen3-vl-abliterated:8b \
  --text-model huihui_ai/qwen3-abliterated:8b \
  --candidates 3
```

## Context File

For repeatable series work, put continuity controls in JSON:

```json
{
  "character_concept": "17-year-old quiet girl, black bob hair, red ribbon.",
  "background_concept": "Rainy nighttime shrine with torii gate, stone pavement, and wet trees.",
  "fixed_elements": [
    "same character identity",
    "same hairstyle",
    "same outfit",
    "red ribbon",
    "rainy night shrine"
  ],
  "allowed_changes": [
    "facial expression",
    "pose",
    "camera angle",
    "panel framing"
  ],
  "forbidden_changes": [
    "different character",
    "different outfit",
    "daytime",
    "modern city background"
  ]
}
```

Run with:

```bash
uv run python -m panel_next \
  --image examples/base.png \
  --context-file examples/context.json \
  --intent "The next panel should show a controlled surprise."
```

CLI values override scalar values from `--context-file`. List values are merged.

## Modes

`--mode full` is the default. It runs image observation and next-panel planning in sequence.

Observe only:

```bash
uv run python -m panel_next \
  --mode observe \
  --image examples/base.png \
  --observation outputs/image_observation.json
```

Plan only from an existing observation:

```bash
uv run python -m panel_next \
  --mode plan \
  --image examples/base.png \
  --observation outputs/image_observation.json \
  --out outputs/next_panel.json \
  --context-file examples/context.json \
  --intent "Use a look-back reaction shot."
```

## CLI Options

- `--image`: input image path. Required.
- `--intent`: optional user intent.
- `--character`: user-authored character concept to preserve.
- `--background`: user-authored background or setting concept to preserve.
- `--fixed`: fixed element that must be preserved. Can be passed multiple times.
- `--allowed`: element that may change freely. Can be passed multiple times.
- `--avoid`: forbidden change or detail to avoid. Can be passed multiple times.
- `--context-file`: JSON file containing continuity controls.
- `--out`: output JSON path. Default: `outputs/next_panel_<timestamp>.json`.
- `--comfyui-dir`: optional directory for ComfyUI prompt text files. Writes positive, negative, and section files per candidate with Windows-friendly CRLF line endings.
- `--tag-lexicon`: optional Danbooru-style tag frequency lexicon as CSV or JSON. CSV columns: `word,frequency`.
- `--observation`: observation JSON path. Default: `outputs/image_observation_<timestamp>.json` in observe/full modes. In plan mode, defaults to the latest `outputs/image_observation*.json`.
- `--vision-model`: Ollama vision model. Default: `huihui_ai/qwen3-vl-abliterated:8b`.
- `--text-model`: Ollama text model. Default: `huihui_ai/qwen3-abliterated:8b`.
- `--ollama-url`: Ollama API URL. Default: `http://localhost:11434`.
- `--candidates`: number of next-panel candidates. Default: `3`.
- `--mode`: `observe`, `plan`, or `full`. Default: `full`.
- `--no-print-prompts`: do not print copy-paste positive/negative prompts to the terminal.
- `--debug`: print intermediate paths and JSON.

## Output JSON Example

```json
{
  "source_image": "examples/base.png",
  "user_intent": "The character notices something behind her.",
  "image_observation": {
    "summary": "...",
    "characters": ["..."],
    "composition": "...",
    "mood": "...",
    "important_visual_details": ["..."],
    "continuity_constraints": ["..."]
  },
  "continuity_control": {
    "character_concept": "17-year-old quiet girl, black bob hair, red ribbon.",
    "background_concept": "Rainy nighttime shrine.",
    "fixed_elements": ["same outfit", "red ribbon"],
    "allowed_changes": ["facial expression", "camera angle"],
    "forbidden_changes": ["different character", "daytime"]
  },
  "next_panels": [
    {
      "panel_id": 1,
      "purpose": "reaction shot",
      "natural_prompt": "English prompt for Anima or image generation model.",
      "prompt_sections": {
        "fixed": "1girl, solo, blonde_hair, long_hair, hair_ribbon, ribbon, white_background",
        "angle": "medium close-up, slight low angle, looking back over shoulder",
        "screen_effects": "soft rain glow, subtle motion emphasis, clean anime linework",
        "situation": "the character notices something behind her and turns with controlled surprise",
        "objects": "wet shrine stones, torii gate, red ribbon, preserved background elements"
      },
      "comfyui_prompt": "1girl, solo, blonde_hair, long_hair, hair_ribbon, ribbon, white_background\nmedium close-up, slight low angle, looking back over shoulder\nsoft rain glow, subtle motion emphasis, clean anime linework\nthe character notices something behind her and turns with controlled surprise\nwet shrine stones, torii gate, red ribbon, preserved background elements",
      "danbooru_tags": ["1girl", "surprised", "looking_back"],
      "camera": "medium close-up, slight low angle",
      "emotion": "surprised but controlled",
      "continuity_note": "Keep the same character design, outfit, lighting, and background elements as the source image.",
      "negative_prompt": "different character, different outfit, extra limbs, distorted hands, low quality",
      "why_this_next": "Japanese explanation of why this panel naturally follows."
    }
  ]
}
```

## Generate ComfyUI Prompts

The following is the same workflow used during local validation. Put a base image under `data/`, then run the full pipeline with continuity controls:

```bash
uv run python -m panel_next \
  --image data/Gy_iDapboAAbPrZ.jpg \
  --out outputs/comfyui_prompt_run.json \
  --comfyui-dir outputs/comfyui_prompts \
  --intent "Create three ComfyUI-friendly next-panel prompts where the character notices the viewer and lightly looks back." \
  --character "same bunny girl character, blonde hair, blue ribbon, light blue bunny ears" \
  --background "plain white background" \
  --fixed "same outfit" \
  --fixed "light blue bunny ears" \
  --fixed "white fur-lined jacket" \
  --fixed "shiny light blue bodysuit" \
  --allowed "facial expression" \
  --allowed "head direction" \
  --allowed "camera angle" \
  --avoid "different character" \
  --avoid "different outfit" \
  --avoid "different hairstyle" \
  --avoid "extra limbs" \
  --candidates 3
```

PowerShell version:

```powershell
uv run python -m panel_next `
  --image data\Gy_iDapboAAbPrZ.jpg `
  --out outputs\comfyui_prompt_run.json `
  --comfyui-dir outputs\comfyui_prompts `
  --intent "Create three ComfyUI-friendly next-panel prompts where the character notices the viewer and lightly looks back." `
  --character "same bunny girl character, blonde hair, blue ribbon, light blue bunny ears" `
  --background "plain white background" `
  --fixed "same outfit" `
  --fixed "light blue bunny ears" `
  --fixed "white fur-lined jacket" `
  --fixed "shiny light blue bodysuit" `
  --allowed "facial expression" `
  --allowed "head direction" `
  --allowed "camera angle" `
  --avoid "different character" `
  --avoid "different outfit" `
  --avoid "different hairstyle" `
  --avoid "extra limbs" `
  --candidates 3
```

The output JSON contains `next_panels[].comfyui_prompt`, which is intended to be copied directly into a ComfyUI positive prompt field. Each prompt is organized as newline-separated lines in this order:

1. fixed continuity tags
2. angle and camera
3. screen effects
4. situation
5. objects, props, and background details

The first line is tag-oriented. The CLI rewrites vague continuity phrases such as `same character`, `same outfit`, and `continuity from source image` into concrete Danbooru-style tags when possible. It uses a small built-in tag frequency table by default. For better results, pass your own tag frequency file:

```csv
word,frequency
1girl,10000000
solo,9000000
blonde_hair,5000000
bunny_ears,1000000
hair_ribbon,1000000
white_background,800000
```

Run with:

```powershell
uv run python -m panel_next `
  --image data\Gy_iDapboAAbPrZ.jpg `
  --tag-lexicon data\danbooru_tags.csv `
  --out outputs\next_panel.json
```

### Production Danbooru Tag CSV

For production use, keep `data/danbooru_tags.csv` in the repository. Regenerate it from Danbooru's tag API when you want a fresher snapshot:

```powershell
uv run python scripts\update_danbooru_tags.py `
  --out data\danbooru_tags.csv `
  --min-count 50 `
  --max-pages 200
```

The generated CSV contains:

```csv
word,frequency,category,is_deprecated
1girl,1234567,0,False
```

If `data/danbooru_tags.csv` exists, `panel-next` loads it automatically. You can also pass a different file with `--tag-lexicon`.

The updater fetches tags ordered by post count and skips empty, deprecated, and very low-frequency tags according to the command options. The generated CSV is about a few MB with the default settings, so it is practical to keep in version control as the baseline tag lexicon.

The CLI also prints progress messages while it is running:

```text
[panel-next] accepted mode=full image=data\Gy_iDapboAAbPrZ.jpg
[panel-next] observing image with vision model: huihui_ai/qwen3-vl-abliterated:8b
[panel-next] observation saved: outputs\image_observation.json
[panel-next] planning 3 next panel candidate(s): huihui_ai/qwen3-abliterated:8b
[panel-next] plan saved: outputs\next_panel.json
```

After planning, it prints copy-paste prompt blocks to the terminal:

```text
=== Candidate 1: reaction shot ===
POSITIVE:
1girl, solo, blonde_hair, long_hair, bunny_ears, hair_ribbon, bodysuit, jacket, white_background
medium close-up, slight low angle, looking back over shoulder
soft rim light, subtle motion emphasis, clean anime linework
the character notices something behind her and turns with controlled surprise
preserve visible accessories, background elements, and important props from the source image
NEGATIVE:
different character, different outfit, extra limbs, distorted hands, low quality
```

Use `--no-print-prompts` if you only want the JSON and optional `--comfyui-dir` text files.

To print only the copy-paste prompts and negative prompts:

```bash
uv run python -c "import json; from pathlib import Path; data=json.loads(Path('outputs/comfyui_prompt_run.json').read_text(encoding='utf-8')); [print('--- candidate {}: {} ---\n{}\nNEGATIVE:\n{}\n'.format(p['panel_id'], p['purpose'], p['comfyui_prompt'], p['negative_prompt'])) for p in data['next_panels']]"
```

When `--comfyui-dir outputs/comfyui_prompts` is used, the CLI also writes Windows-friendly UTF-8 text files:

```text
outputs/comfyui_prompts/candidate_01_positive.txt
outputs/comfyui_prompts/candidate_01_negative.txt
outputs/comfyui_prompts/candidate_01_sections.txt
```

Open `candidate_01_positive.txt` and paste it into the ComfyUI positive prompt field. Open `candidate_01_negative.txt` and paste it into the negative prompt field. The `sections` file keeps the fixed text, angle, effects, situation, and object/background lines labeled for manual editing.

Example generated positive prompt:

```text
1girl, solo, blonde_hair, long_hair, bunny_ears, hair_ribbon, bodysuit, jacket, white_background
medium close-up, slight low angle, looking back over shoulder
soft rim light, subtle motion emphasis, clean anime linework
the character notices something behind her and turns with controlled surprise
preserve visible accessories, background elements, and important props from the source image
```

Example negative prompt:

```text
different character, different outfit, extra limbs, distorted hands, low quality
```

## Future ComfyUI / Anima Integration

This MVP intentionally stops at JSON planning. A later layer can read `outputs/next_panel.json`, select one `next_panels` item, and copy `comfyui_prompt` directly into a ComfyUI prompt field. The same item also includes `prompt_sections` so fixed continuity text, angle, screen effects, situation, and object/background details can be edited independently.

## Troubleshooting

- `Could not connect to Ollama`: start Ollama with `ollama serve` and check `--ollama-url`.
- `model not found`: run `ollama list`, then pass the exact model name with `--vision-model` or `--text-model`.
- `Failed to parse ... JSON`: the raw LLM response is saved to `outputs/debug_last_response.txt`.
- `Input image does not exist`: check the `--image` path.
- `Context file is not valid JSON`: check `--context-file`.
- Unsupported image format: use PNG, JPG, JPEG, or WEBP.

## Tests

```bash
uv run pytest
```

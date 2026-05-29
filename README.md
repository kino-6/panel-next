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

Or install with standard Python tooling:

```bash
python -m pip install -e .
```

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
python -m panel_next --image examples/base.png --vision-model your-vl-model:tag
```

## Usage

Full pipeline:

```bash
python -m panel_next \
  --image examples/base.png \
  --intent "Make the next panel a natural surprised look-back beat." \
  --out outputs/next_panel.json
```

PowerShell uses a backtick for line continuation, not `\`:

```powershell
python -m panel_next `
  --image examples/base.png `
  --intent "Make the next panel a natural surprised look-back beat." `
  --out outputs/next_panel.json
```

You can also run it as a single line:

```powershell
python -m panel_next --image examples/base.png --intent "Make the next panel a natural surprised look-back beat." --out outputs/next_panel.json
```

With explicit continuity controls:

```bash
python -m panel_next \
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
python -m panel_next \
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
python -m panel_next \
  --image examples/base.png \
  --context-file examples/context.json \
  --intent "The next panel should show a controlled surprise."
```

CLI values override scalar values from `--context-file`. List values are merged.

## Modes

`--mode full` is the default. It runs image observation and next-panel planning in sequence.

Observe only:

```bash
python -m panel_next \
  --mode observe \
  --image examples/base.png \
  --observation outputs/image_observation.json
```

Plan only from an existing observation:

```bash
python -m panel_next \
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
- `--out`: output JSON path. Default: `outputs/next_panel.json`.
- `--comfyui-dir`: optional directory for ComfyUI prompt text files. Writes positive, negative, and section files per candidate with Windows-friendly CRLF line endings.
- `--observation`: observation JSON path. Default: `outputs/image_observation.json`.
- `--vision-model`: Ollama vision model. Default: `huihui_ai/qwen3-vl-abliterated:8b`.
- `--text-model`: Ollama text model. Default: `huihui_ai/qwen3-abliterated:8b`.
- `--ollama-url`: Ollama API URL. Default: `http://localhost:11434`.
- `--candidates`: number of next-panel candidates. Default: `3`.
- `--mode`: `observe`, `plan`, or `full`. Default: `full`.
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
        "fixed": "same character, same outfit, same hairstyle, red ribbon, continuity from source image",
        "angle": "medium close-up, slight low angle, looking back over shoulder",
        "screen_effects": "soft rain glow, subtle motion emphasis, clean anime linework",
        "situation": "the character notices something behind her and turns with controlled surprise",
        "objects": "wet shrine stones, torii gate, red ribbon, preserved background elements"
      },
      "comfyui_prompt": "same character, same outfit, same hairstyle, red ribbon, continuity from source image\nmedium close-up, slight low angle, looking back over shoulder\nsoft rain glow, subtle motion emphasis, clean anime linework\nthe character notices something behind her and turns with controlled surprise\nwet shrine stones, torii gate, red ribbon, preserved background elements",
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

1. fixed continuity text
2. angle and camera
3. screen effects
4. situation
5. objects, props, and background details

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
same character, same outfit, same hairstyle, continuity from source image
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

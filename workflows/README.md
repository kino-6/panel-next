# ComfyUI Workflows

Place ComfyUI API workflow templates here.

The exporter expects ComfyUI's API prompt format: a JSON object keyed by node id. The positive and negative prompt nodes should be `CLIPTextEncode`-style nodes with `inputs.text`.

Minimal shape:

```json
{
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "positive prompt",
      "clip": ["4", 1]
    }
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "negative prompt",
      "clip": ["4", 1]
    }
  }
}
```

Export a candidate into a template:

```powershell
uv run python -m panel_next export-comfyui `
  --plan outputs\next_panel_20260530_010122.json `
  --candidate 1 `
  --template workflows\comfyui_api_template.json `
  --positive-node 6 `
  --negative-node 7 `
  --out outputs\comfyui_candidate_01.json
```

The exporter only changes `inputs.text` on the two nodes you specify. It leaves the rest of the workflow untouched.

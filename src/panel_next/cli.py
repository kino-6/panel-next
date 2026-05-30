from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .context import build_continuity_control
from .comfyui_export import ComfyUIExportConfig, ComfyUIExportError, export_comfyui_workflow
from .image_io import ImageInputError
from .ollama_client import OllamaError
from .ollama_client import OllamaClient
from .pipeline import (
    PipelineConfig,
    print_prompt_blocks,
    print_summary,
    run_observe,
    run_plan,
)
from .tag_lexicon import load_tag_frequencies


DEFAULT_TEXT_MODEL = "huihui_ai/qwen3-abliterated:8b"
DEFAULT_VISION_MODEL = "huihui_ai/qwen3-vl-abliterated:8b"
DEFAULT_TAG_LEXICON = Path("data/danbooru_tags.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="panel-next",
        description="Plan the next storyboard panel from a base image using Ollama.",
    )
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--intent", default="", help="User intent for the next panel.")
    parser.add_argument(
        "--character",
        default="",
        help="User-authored character concept to preserve.",
    )
    parser.add_argument(
        "--background",
        default="",
        help="User-authored background or setting concept to preserve.",
    )
    parser.add_argument(
        "--fixed",
        action="append",
        default=[],
        help="Fixed element that must be preserved. Can be passed multiple times.",
    )
    parser.add_argument(
        "--allowed",
        action="append",
        default=[],
        help="Element that may change freely. Can be passed multiple times.",
    )
    parser.add_argument(
        "--avoid",
        action="append",
        default=[],
        help="Forbidden change or detail to avoid. Can be passed multiple times.",
    )
    parser.add_argument(
        "--context-file",
        default=None,
        help=(
            "JSON file with character_concept, background_concept, fixed_elements, "
            "allowed_changes, and forbidden_changes."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Output JSON path. Default: outputs/next_panel_<timestamp>.json "
            "for plan/full modes."
        ),
    )
    parser.add_argument(
        "--comfyui-dir",
        default=None,
        help=(
            "Optional directory for Windows-friendly ComfyUI prompt text files "
            "(positive, negative, and section files per candidate)."
        ),
    )
    parser.add_argument(
        "--tag-lexicon",
        default=None,
        help=(
            "Optional Danbooru-style tag frequency lexicon as CSV or JSON. "
            "CSV columns: word,frequency."
        ),
    )
    parser.add_argument(
        "--observation",
        default=None,
        help=(
            "Observation JSON path. Used as output in observe mode and input in plan mode. "
            "Default: outputs/image_observation_<timestamp>.json for observe/full modes. "
            "Required in plan mode."
        ),
    )
    parser.add_argument(
        "--vision-model",
        default=DEFAULT_VISION_MODEL,
        help=f"Vision Ollama model. Default: {DEFAULT_VISION_MODEL}",
    )
    parser.add_argument(
        "--text-model",
        default=DEFAULT_TEXT_MODEL,
        help=f"Text Ollama model. Default: {DEFAULT_TEXT_MODEL}",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama API URL. Default: http://localhost:11434",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=3,
        help="Number of next panel candidates. Default: 3",
    )
    parser.add_argument(
        "--mode",
        choices=("observe", "plan", "full"),
        default="full",
        help="Run observe only, plan only, or full pipeline. Default: full",
    )
    parser.add_argument(
        "--no-print-prompts",
        action="store_true",
        help="Do not print copy-paste positive/negative prompts to the terminal.",
    )
    parser.add_argument("--debug", action="store_true", help="Print intermediate results.")
    return parser


def build_export_comfyui_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="panel-next export-comfyui",
        description="Export a ComfyUI API workflow JSON from a panel-next plan.",
    )
    parser.add_argument("--plan", required=True, help="panel-next output JSON path.")
    parser.add_argument("--template", required=True, help="ComfyUI API workflow template JSON path.")
    parser.add_argument("--candidate", type=int, default=1, help="Candidate panel id or 1-based index. Default: 1")
    parser.add_argument("--positive-node", required=True, help="Positive CLIPTextEncode node id.")
    parser.add_argument("--negative-node", required=True, help="Negative CLIPTextEncode node id.")
    parser.add_argument(
        "--out",
        required=True,
        help="Output ComfyUI workflow JSON path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "export-comfyui":
        return export_comfyui_main(argv[1:])

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.candidates < 1:
        parser.error("--candidates must be 1 or greater.")
    if args.mode == "plan" and not args.observation:
        parser.error("--observation is required when --mode plan is used.")

    try:
        continuity_control = build_continuity_control(
            character_concept=args.character,
            background_concept=args.background,
            fixed_elements=args.fixed,
            allowed_changes=args.allowed,
            forbidden_changes=args.avoid,
            context_file=args.context_file,
        )
        tag_lexicon = _resolve_tag_lexicon(args.tag_lexicon)
        tag_frequencies = load_tag_frequencies(tag_lexicon)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config = PipelineConfig(
            image=Path(args.image),
            intent=args.intent,
            out=_resolve_output_path(args.out, args.mode, timestamp),
            observation=_resolve_observation_path(args.observation, args.mode, timestamp),
            vision_model=args.vision_model,
            text_model=args.text_model,
            ollama_url=args.ollama_url,
            candidates=args.candidates,
            continuity_control=continuity_control,
            comfyui_dir=Path(args.comfyui_dir) if args.comfyui_dir else None,
            tag_lexicon=tag_lexicon,
            tag_frequencies=tag_frequencies,
            debug=args.debug,
        )
        result = _run_with_progress(args.mode, config)
        if args.debug:
            print(f"Mode: {args.mode}")
            print(f"Observation path: {config.observation}")
            print(f"Output path: {config.out}")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        print_summary(result, args.mode)
        if args.mode != "observe" and not args.no_print_prompts:
            print_prompt_blocks(result)
        if args.mode != "observe" and config.comfyui_dir is not None:
            print(f"ComfyUI prompt files saved to: {config.comfyui_dir}")
    except (ImageInputError, FileNotFoundError, ValueError, OllamaError) as exc:
        print(f"panel-next error: {exc}", file=sys.stderr)
        return 1
    return 0


def export_comfyui_main(argv: list[str] | None = None) -> int:
    parser = build_export_comfyui_parser()
    args = parser.parse_args(argv)
    config = ComfyUIExportConfig(
        plan=Path(args.plan),
        template=Path(args.template),
        out=Path(args.out),
        candidate=args.candidate,
        positive_node=str(args.positive_node),
        negative_node=str(args.negative_node),
    )
    try:
        export_comfyui_workflow(config)
    except (ComfyUIExportError, FileNotFoundError) as exc:
        print(f"panel-next export-comfyui error: {exc}", file=sys.stderr)
        return 1
    print(f"ComfyUI workflow saved to: {config.out}")
    return 0


def _run_with_progress(mode: str, config: PipelineConfig):
    _progress(f"accepted mode={mode} image={config.image}")
    if mode == "observe":
        _progress(f"observing image with vision model: {config.vision_model}")
        result = run_observe(config)
        _progress(f"observation saved: {config.observation}")
        return result
    if mode == "plan":
        _progress(f"using observation: {config.observation}")
        _progress(f"planning next panels with text model: {config.text_model}")
        result = run_plan(config)
        _progress(f"plan saved: {config.out}")
        return result

    client = OllamaClient(config.ollama_url)
    _progress(f"observing image with vision model: {config.vision_model}")
    observation = run_observe(config, client=client)
    _progress(f"observation saved: {config.observation}")
    _progress(f"planning {config.candidates} next panel candidate(s): {config.text_model}")
    result = run_plan(config, image_observation=observation, client=client)
    _progress(f"plan saved: {config.out}")
    return result


def _progress(message: str) -> None:
    print(f"[panel-next] {message}", file=sys.stderr, flush=True)


def _resolve_tag_lexicon(path: str | None) -> Path | None:
    if path:
        return Path(path)
    if DEFAULT_TAG_LEXICON.exists():
        return DEFAULT_TAG_LEXICON
    return None


def _resolve_output_path(path: str | None, mode: str, timestamp: str) -> Path:
    if path:
        return Path(path)
    if mode == "observe":
        return Path(f"outputs/next_panel_{timestamp}.json")
    return Path(f"outputs/next_panel_{timestamp}.json")


def _resolve_observation_path(path: str | None, mode: str, timestamp: str) -> Path:
    if path:
        return Path(path)
    if mode == "plan":
        raise ValueError("--observation is required when --mode plan is used.")
    return Path(f"outputs/image_observation_{timestamp}.json")

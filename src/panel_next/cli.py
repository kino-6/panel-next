from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import build_continuity_control
from .image_io import ImageInputError
from .ollama_client import OllamaError
from .pipeline import PipelineConfig, print_summary, run_full, run_observe, run_plan


DEFAULT_TEXT_MODEL = "huihui_ai/qwen3-abliterated:8b"
DEFAULT_VISION_MODEL = "huihui_ai/qwen3-vl-abliterated:8b"


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
        default="outputs/next_panel.json",
        help="Output JSON path. Default: outputs/next_panel.json",
    )
    parser.add_argument(
        "--observation",
        default="outputs/image_observation.json",
        help=(
            "Observation JSON path. Used as output in observe mode and input in plan mode. "
            "Default: outputs/image_observation.json"
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
    parser.add_argument("--debug", action="store_true", help="Print intermediate results.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.candidates < 1:
        parser.error("--candidates must be 1 or greater.")

    try:
        continuity_control = build_continuity_control(
            character_concept=args.character,
            background_concept=args.background,
            fixed_elements=args.fixed,
            allowed_changes=args.allowed,
            forbidden_changes=args.avoid,
            context_file=args.context_file,
        )
        config = PipelineConfig(
            image=Path(args.image),
            intent=args.intent,
            out=Path(args.out),
            observation=Path(args.observation),
            vision_model=args.vision_model,
            text_model=args.text_model,
            ollama_url=args.ollama_url,
            candidates=args.candidates,
            continuity_control=continuity_control,
            debug=args.debug,
        )
        if args.mode == "observe":
            result = run_observe(config)
        elif args.mode == "plan":
            result = run_plan(config)
        else:
            result = run_full(config)
        if args.debug:
            print(f"Mode: {args.mode}")
            print(f"Observation path: {config.observation}")
            print(f"Output path: {config.out}")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        print_summary(result, args.mode)
    except (ImageInputError, FileNotFoundError, ValueError, OllamaError) as exc:
        print(f"panel-next error: {exc}", file=sys.stderr)
        return 1
    return 0

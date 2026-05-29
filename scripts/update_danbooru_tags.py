from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://danbooru.donmai.us"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Danbooru tag counts and write a panel-next tag lexicon CSV."
    )
    parser.add_argument(
        "--out",
        default="data/danbooru_tags.csv",
        help="Output CSV path. Default: data/danbooru_tags.csv",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Danbooru base URL. Default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Tags per API request. Default: 1000",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum API pages to fetch. Default: 200",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=50,
        help="Stop keeping tags below this post count. Default: 50",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds to sleep between requests. Default: 0.5",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = Path(args.out)
    rows = fetch_tags(
        base_url=args.base_url,
        limit=args.limit,
        max_pages=args.max_pages,
        min_count=args.min_count,
        sleep_seconds=args.sleep,
    )
    write_csv(output_path, rows)
    print(f"Wrote {len(rows)} tags to {output_path}")
    return 0


def fetch_tags(
    base_url: str,
    limit: int,
    max_pages: int,
    min_count: int,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        page_rows = fetch_tag_page(base_url=base_url, limit=limit, page=page)
        if not page_rows:
            break
        kept = 0
        for tag in page_rows:
            post_count = int(tag.get("post_count") or 0)
            if post_count < min_count:
                continue
            name = tag.get("name")
            if not name:
                continue
            rows.append(
                {
                    "word": str(name),
                    "frequency": post_count,
                    "category": tag.get("category", ""),
                    "is_deprecated": tag.get("is_deprecated", False),
                }
            )
            kept += 1
        print(f"Fetched page {page}: {len(page_rows)} tags, kept {kept}")
        if kept == 0:
            break
        time.sleep(sleep_seconds)
    return rows


def fetch_tag_page(base_url: str, limit: int, page: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "search[hide_empty]": "yes",
            "search[is_deprecated]": "false",
            "search[order]": "count",
            "limit": str(limit),
            "page": str(page),
        }
    )
    url = f"{base_url.rstrip('/')}/tags.json?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "panel-next tag updater",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError(f"Unexpected Danbooru response shape: {data!r}")
    return data


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["word", "frequency", "category", "is_deprecated"],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())

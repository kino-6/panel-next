from __future__ import annotations

import base64
from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class ImageInputError(ValueError):
    """Raised when the input image cannot be used."""


def validate_image_path(image_path: str | Path) -> Path:
    path = Path(image_path)
    if not path.exists():
        raise ImageInputError(f"Input image does not exist: {path}")
    if not path.is_file():
        raise ImageInputError(f"Input image is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ImageInputError(
            f"Unsupported image extension '{path.suffix}'. Supported: {supported}"
        )
    return path


def encode_image_base64(image_path: str | Path) -> str:
    path = validate_image_path(image_path)
    return base64.b64encode(path.read_bytes()).decode("ascii")

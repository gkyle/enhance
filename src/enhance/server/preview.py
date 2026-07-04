"""8-bit preview generation for the browser.

The Qt `CanvasLabel` loaded 8-bit images with cv2 for display. Browsers can't
render 16-bit TIFFs, so we generate 8-bit PNG previews here, write them into a
cache directory, and return a URL that resolves against the `/cache` static mount
(served over http://127.0.0.1). Filenames are content/size hashed so identical
requests reuse an existing file.
"""

import hashlib
import logging
import os
from typing import Optional, Tuple

import cv2

logger = logging.getLogger(__name__)

# Cache directory for generated previews, served via the /cache static mount.
PREVIEW_CACHE_DIR = os.path.join(os.getcwd(), ".preview_cache")
CACHE_URL_PREFIX = "/cache"


def ensure_cache_dir() -> str:
    os.makedirs(PREVIEW_CACHE_DIR, exist_ok=True)
    return PREVIEW_CACHE_DIR


def _preview_name(src_path: str, max_w: Optional[int], max_h: Optional[int]) -> str:
    try:
        mtime = os.path.getmtime(src_path)
    except OSError:
        mtime = 0
    key = f"{src_path}|{mtime}|{max_w}|{max_h}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"{digest}.png"


def generate_preview(
    src_path: str,
    max_w: Optional[int] = None,
    max_h: Optional[int] = None,
) -> Tuple[str, int, int]:
    """Generate (or reuse) an 8-bit PNG preview.

    Returns (url, width, height). `url` is relative to the server origin, e.g.
    "/cache/<hash>.png".
    """
    ensure_cache_dir()
    name = _preview_name(src_path, max_w, max_h)
    out_path = os.path.join(PREVIEW_CACHE_DIR, name)

    # cv2.imread (without UNCHANGED) returns an 8-bit BGR image, downconverting
    # 16-bit sources — exactly what CanvasLabel relied on for display.
    if not os.path.exists(out_path):
        img = cv2.imread(src_path)
        if img is None:
            raise FileNotFoundError(f"Could not read image: {src_path}")

        h, w = img.shape[:2]
        if max_w or max_h:
            scale = min(
                (max_w / w) if max_w else 1.0,
                (max_h / h) if max_h else 1.0,
                1.0,
            )
            if scale < 1.0:
                interpolation = cv2.INTER_AREA
                img = cv2.resize(
                    img, (max(1, int(w * scale)), max(1, int(h * scale))),
                    interpolation=interpolation,
                )
        cv2.imwrite(out_path, img)

    written = cv2.imread(out_path)
    ph, pw = written.shape[:2]
    return f"{CACHE_URL_PREFIX}/{name}", pw, ph


def clear_preview_cache() -> None:
    if not os.path.isdir(PREVIEW_CACHE_DIR):
        return
    for name in os.listdir(PREVIEW_CACHE_DIR):
        try:
            os.remove(os.path.join(PREVIEW_CACHE_DIR, name))
        except OSError as e:  # pragma: no cover - defensive
            logger.warning("Failed to remove preview %s: %s", name, e)

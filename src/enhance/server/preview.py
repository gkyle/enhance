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
import numpy as np

logger = logging.getLogger(__name__)

# Cache directory for generated previews, served via the /cache static mount.
PREVIEW_CACHE_DIR = os.path.join(os.getcwd(), ".preview_cache")
CACHE_URL_PREFIX = "/cache"

# RGB colors used to tint mask overlays, cycled by mask index. These match the
# canvas.js MASK_COLORS palette so an overlay's fill matches its box/label color.
MASK_COLORS = [
    (66, 135, 245),   # blue
    (80, 200, 120),   # green
    (231, 76, 60),    # red
    (52, 152, 219),   # light blue
    (155, 89, 182),   # purple
    (212, 188, 60),   # yellow
]


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


def generate_mask_overlay(
    file_id: str,
    version: int,
    index: int,
    mask_array,
) -> Tuple[str, int, int]:
    """Render a boolean mask as a translucent colored RGBA PNG.

    Returns (url, width, height). The overlay matches the mask array's pixel
    dimensions (the full-res image size), so the renderer can draw it using the
    same transform as the base preview. `version` invalidates the cache when
    masks are regenerated. Mirrors CanvasLabel.applyMasks' color fill.
    """
    ensure_cache_dir()
    name = f"mask_{file_id}_{version}_{index}.png"
    out_path = os.path.join(PREVIEW_CACHE_DIR, name)

    arr = np.asarray(mask_array)
    if arr.ndim != 2:
        arr = np.squeeze(arr)
    h, w = arr.shape[:2]

    if not os.path.exists(out_path):
        color = MASK_COLORS[index % len(MASK_COLORS)]
        r, g, b = color
        # cv2 writes 4-channel arrays as BGRA, so fill in BGRA order to make the
        # browser read back the intended RGB (matching the canvas box color).
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        sel = arr.astype(bool)
        rgba[sel, 0] = b
        rgba[sel, 1] = g
        rgba[sel, 2] = r
        rgba[sel, 3] = 110  # ~0.43 alpha
        cv2.imwrite(out_path, rgba)

    return f"{CACHE_URL_PREFIX}/{name}", w, h


def mask_color(index: int) -> Tuple[int, int, int]:
    """RGB color for a mask index (matches the overlay tint)."""
    return MASK_COLORS[index % len(MASK_COLORS)]

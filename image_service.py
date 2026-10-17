"""Basic image processing and feature extraction."""

from pathlib import Path
from typing import Dict, Any
from PIL import Image
import hashlib


def get_image_info(filepath: Path) -> Dict[str, Any]:
    """Return basic image metadata."""
    info: Dict[str, Any] = {}
    try:
        with Image.open(filepath) as img:
            info["width"] = img.width
            info["height"] = img.height
            info["format"] = img.format
            info["mode"] = img.mode
            info["size_bytes"] = filepath.stat().st_size

            # Simple perceptual hash for later matching (very basic)
            small = img.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
            pixels = list(small.getdata())
            avg = sum(pixels) / len(pixels)
            bits = "".join("1" if p > avg else "0" for p in pixels)
            info["phash"] = hashlib.md5(bits.encode()).hexdigest()[:16]
    except Exception as e:
        info["error"] = str(e)
    return info


def process_image(filepath: Path) -> Dict[str, Any]:
    """
    Placeholder for more advanced processing.
    In a full port this would call imgprep.py style crops, edge detection, etc.
    """
    result: Dict[str, Any] = {
        "note": "Basic processing only. Advanced features (pier detection, skyline extraction, CLIP embeddings) require additional models.",
        "crops": [],
        "features": {},
    }

    try:
        with Image.open(filepath) as img:
            w, h = img.size
            result["features"]["aspect_ratio"] = round(w / h, 3)
            result["features"]["megapixels"] = round((w * h) / 1_000_000, 2)

            # Simple brightness / contrast stats
            gray = img.convert("L")
            pixels = list(gray.getdata())
            if pixels:
                avg = sum(pixels) / len(pixels)
                result["features"]["avg_brightness"] = round(avg, 1)
                result["features"]["is_dark"] = avg < 60
                result["features"]["is_bright"] = avg > 180
    except Exception as e:
        result["error"] = str(e)

    return result

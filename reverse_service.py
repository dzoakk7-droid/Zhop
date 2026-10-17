"""
Reverse image search — limited web version.

Full geo-sleuth uses Playwright + Baidu/Yandex and can handle CAPTCHAs / complex flows.
In a pure web backend we can only do limited checks or call external APIs.
This is a stub that returns honest status + suggestions.
"""

from pathlib import Path
from typing import Dict, Any
import httpx


async def reverse_image_search_stub(filepath: Path) -> Dict[str, Any]:
    """
    Placeholder for reverse image search.
    Real implementation would need:
    - Playwright / browser automation (Baidu, Yandex)
    - Or paid APIs (Google Vision, TinEye, SerpAPI, etc.)
    """
    return {
        "status": "limited",
        "note": (
            "Full reverse image search (Baidu + Yandex via browser automation) "
            "is not available in this web demo. "
            "In the original geo-sleuth this step uses Playwright and can return "
            "similar images + possible location clues."
        ),
        "suggestions": [
            "Upload the photo to Yandex Images or Google Lens manually",
            "Check if the photo appears on social media / mapping sites",
            "Look for unique objects (signs, architecture, vegetation) and search by description",
        ],
        "engines": {
            "yandex": "https://yandex.com/images/",
            "google_lens": "https://lens.google.com/",
            "bing": "https://www.bing.com/visualsearch",
        },
    }


# Future: real implementations could go here
# async def reverse_yandex(...): ...
# async def reverse_baidu(...): ...

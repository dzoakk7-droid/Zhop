"""EXIF extraction service."""

from pathlib import Path
from typing import Dict, Any, Optional
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def _convert_to_degrees(value) -> Optional[float]:
    """Convert GPS coordinates to decimal degrees."""
    try:
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None


def extract_exif(filepath: Path) -> Dict[str, Any]:
    """Extract useful EXIF data including GPS."""
    result: Dict[str, Any] = {
        "gps": None,
        "datetime": None,
        "camera": None,
        "lens": None,
        "focal_length": None,
        "orientation": None,
        "raw_tags": {},
    }

    # Method 1: exifread (more reliable for GPS)
    try:
        with open(filepath, "rb") as f:
            tags = exifread.process_file(f, details=False)

        # GPS
        lat = tags.get("GPS GPSLatitude")
        lat_ref = tags.get("GPS GPSLatitudeRef")
        lon = tags.get("GPS GPSLongitude")
        lon_ref = tags.get("GPS GPSLongitudeRef")
        alt = tags.get("GPS GPSAltitude")

        if lat and lon and lat_ref and lon_ref:
            lat_val = _convert_to_degrees(lat)
            lon_val = _convert_to_degrees(lon)
            if lat_val is not None and lon_val is not None:
                if str(lat_ref) == "S":
                    lat_val = -lat_val
                if str(lon_ref) == "W":
                    lon_val = -lon_val
                result["gps"] = {
                    "lat": lat_val,
                    "lon": lon_val,
                    "altitude": None,
                }
                if alt:
                    try:
                        result["gps"]["altitude"] = float(alt.values[0].num) / float(alt.values[0].den)
                    except Exception:
                        pass

        # Datetime
        for key in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            if key in tags:
                result["datetime"] = str(tags[key])
                break

        # Camera
        make = tags.get("Image Make")
        model = tags.get("Image Model")
        if make or model:
            result["camera"] = f"{make or ''} {model or ''}".strip()

        # Focal length
        fl = tags.get("EXIF FocalLength")
        if fl:
            try:
                result["focal_length"] = f"{float(fl.values[0].num)/float(fl.values[0].den):.1f} mm"
            except Exception:
                result["focal_length"] = str(fl)

        # Orientation
        orient = tags.get("Image Orientation")
        if orient:
            result["orientation"] = str(orient)

        # Keep a few raw interesting tags
        for k, v in list(tags.items())[:30]:
            result["raw_tags"][str(k)] = str(v)

    except Exception as e:
        result["error_exifread"] = str(e)

    # Fallback / enrichment with Pillow
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTime" and not result["datetime"]:
                        result["datetime"] = str(value)
                    if tag == "Make" and not result.get("camera"):
                        result["camera"] = str(value)
                    if tag == "Model" and result.get("camera") and str(value) not in result["camera"]:
                        result["camera"] = f"{result['camera']} {value}".strip()
    except Exception:
        pass

    return result

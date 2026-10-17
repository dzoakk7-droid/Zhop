"""OpenStreetMap Overpass queries."""

from typing import Dict, Any, Optional, List
import httpx


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


async def query_nearby(lat: float, lon: float, radius: int = 300) -> Dict[str, Any]:
    """Query interesting features near a point."""
    query = f"""
    [out:json][timeout:25];
    (
      node["name"](around:{radius},{lat},{lon});
      way["name"](around:{radius},{lat},{lon});
      node["amenity"](around:{radius},{lat},{lon});
      node["tourism"](around:{radius},{lat},{lon});
      node["historic"](around:{radius},{lat},{lon});
      way["building"](around:{radius},{lat},{lon});
      way["highway"](around:{radius},{lat},{lon});
    );
    out center 30;
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()

        places = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name and not tags.get("amenity") and not tags.get("tourism"):
                continue
            center = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            places.append({
                "id": el.get("id"),
                "type": el.get("type"),
                "name": name,
                "tags": {k: v for k, v in tags.items() if k in (
                    "name", "amenity", "tourism", "historic", "shop",
                    "highway", "building", "addr:street", "addr:housenumber"
                )},
                "lat": center.get("lat"),
                "lon": center.get("lon"),
            })

        return {
            "query_center": {"lat": lat, "lon": lon},
            "radius_m": radius,
            "places": places[:25],
            "count": len(places),
        }
    except Exception as e:
        return {"error": str(e), "places": []}


async def search_places(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple Nominatim search (for future use)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "GeoSleuthWeb/0.1 (educational)"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return [{"error": str(e)}]

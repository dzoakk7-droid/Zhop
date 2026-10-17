"""
GeoSleuth Web — simplified but feature-rich photo geolocation web app.
Inspired by https://github.com/Oldcircle/geo-sleuth
"""

import os
import uuid
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from services.exif_service import extract_exif
from services.image_service import process_image, get_image_info
from services.osm_service import query_nearby, search_places
from services.reverse_service import reverse_image_search_stub

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="GeoSleuth Web",
    description="Photo geolocation assistant (inspired by geo-sleuth)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# In-memory job store (for demo; use Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Accept photo, save it, start analysis pipeline."""
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse({"error": "Only image files are allowed"}, status_code=400)

    job_id = str(uuid.uuid4())
    ext = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}:
        ext = ".jpg"

    filename = f"{job_id}{ext}"
    filepath = UPLOAD_DIR / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Initialize job
    jobs[job_id] = {
        "id": job_id,
        "status": "processing",
        "filename": filename,
        "original_name": file.filename,
        "created_at": time.time(),
        "steps": [],
        "result": None,
        "error": None,
    }

    # Run analysis in background
    background_tasks.add_task(run_analysis, job_id, filepath)

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return job


@app.get("/result/{job_id}", response_class=HTMLResponse)
async def result_page(request: Request, job_id: str):
    job = jobs.get(job_id)
    if not job:
        return HTMLResponse("<h1>Job not found</h1>", status_code=404)
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "job": job, "job_id": job_id},
    )


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------

async def run_analysis(job_id: str, filepath: Path):
    """Main analysis pipeline — modular so more geo-sleuth features can be added."""
    job = jobs[job_id]
    steps = job["steps"]

    try:
        # Step 1: Basic image info
        steps.append({"name": "image_info", "status": "running", "message": "Reading image..."})
        info = get_image_info(filepath)
        steps[-1].update({"status": "done", "data": info})

        # Step 2: EXIF
        steps.append({"name": "exif", "status": "running", "message": "Extracting EXIF metadata..."})
        exif_data = extract_exif(filepath)
        steps[-1].update({"status": "done", "data": exif_data})

        # Step 3: Image processing / features
        steps.append({"name": "process", "status": "running", "message": "Processing image features..."})
        processed = process_image(filepath)
        steps[-1].update({"status": "done", "data": processed})

        # Step 4: Reverse image search (stub / limited)
        steps.append({"name": "reverse", "status": "running", "message": "Running reverse image search..."})
        reverse_results = await reverse_image_search_stub(filepath)
        steps[-1].update({"status": "done", "data": reverse_results})

        # Step 5: If GPS present — query nearby OSM
        gps = exif_data.get("gps")
        osm_data = None
        if gps and gps.get("lat") and gps.get("lon"):
            steps.append({"name": "osm", "status": "running", "message": "Querying OpenStreetMap nearby..."})
            osm_data = await query_nearby(gps["lat"], gps["lon"])
            steps[-1].update({"status": "done", "data": osm_data})
        else:
            steps.append({
                "name": "osm",
                "status": "skipped",
                "message": "No GPS in EXIF — OSM nearby query skipped. Full skyline / region scan requires more advanced modules."
            })

        # Build final result summary
        result = {
            "image_url": f"/uploads/{filepath.name}",
            "exif": exif_data,
            "image_info": info,
            "processed": processed,
            "reverse_search": reverse_results,
            "osm": osm_data,
            "confidence": "high" if gps else "low",
            "summary": build_summary(exif_data, reverse_results, osm_data),
        }

        job["result"] = result
        job["status"] = "done"

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        steps.append({"name": "error", "status": "error", "message": str(e)})


def build_summary(exif: dict, reverse: dict, osm: Optional[dict]) -> str:
    parts = []

    gps = exif.get("gps")
    if gps and gps.get("lat") and gps.get("lon"):
        parts.append(f"📍 GPS found in EXIF: {gps['lat']:.6f}, {gps['lon']:.6f}")
        if gps.get("altitude"):
            parts.append(f"Altitude: {gps['altitude']} m")
    else:
        parts.append("📍 No GPS coordinates found in EXIF metadata.")

    if exif.get("datetime"):
        parts.append(f"📅 Capture time: {exif['datetime']}")

    if exif.get("camera"):
        parts.append(f"📷 Camera: {exif['camera']}")

    if reverse and reverse.get("note"):
        parts.append(f"🔍 {reverse['note']}")

    if osm and osm.get("places"):
        places = osm["places"][:5]
        names = [p.get("name") or p.get("tags", {}).get("name", "unnamed") for p in places]
        parts.append(f"🗺️ Nearby places: {', '.join(names)}")

    parts.append(
        "\n⚠️ This is a simplified web version. Full geo-sleuth capabilities "
        "(skyline matching, CLIP satellite ranking, pier spacing geometry, etc.) "
        "require the original local skill + powerful compute."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "jobs": len(jobs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

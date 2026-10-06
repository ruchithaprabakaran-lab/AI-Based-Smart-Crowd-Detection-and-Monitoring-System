"""
Smart Crowd Detection and Monitoring System
FastAPI Backend Application
"""

import os
import io
import time
import uuid
import json
import base64
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.detector import (
    process_image_bytes,
    detect_people,
    render_annotated_image,
    generate_density_heatmap,
    encode_image_base64
)
from app.density_classifier import classify_crowd_density, EVENT_PRESETS
from app.alert_engine import generate_crowd_alert
from app.database import (
    init_db,
    save_detection_record,
    save_time_series_point,
    get_detection_history,
    get_analytics_summary,
    clear_history
)

import cv2
import numpy as np

# Create FastAPI app
app = FastAPI(
    title="Smart Crowd Detection and Monitoring System",
    description="AI-powered crowd density estimation, monitoring, and early warning dashboard.",
    version="1.0.0"
)

# Enable CORS for browser interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
SAMPLES_DIR = os.path.join(STATIC_DIR, "samples")

os.makedirs(SAMPLES_DIR, exist_ok=True)

# Initialize database
init_db()

@app.on_event("startup")
def startup_event():
    init_db()


class LiveFramePayload(BaseModel):
    image_base64: str
    event_type: str = "other"
    privacy_mode: bool = True
    conf_threshold: float = 0.25
    custom_low: Optional[int] = None
    custom_medium: Optional[int] = None
    custom_high: Optional[int] = None
    session_id: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Smart Crowd Detection and Monitoring System"}


@app.get("/api/event-types")
def get_event_types():
    """Return all supported event types and default thresholds."""
    return {"events": EVENT_PRESETS}


@app.get("/api/samples")
def list_sample_presets():
    """List preloaded demonstration samples for 1-click test."""
    samples = [
        {
            "id": "temple-gathering",
            "name": "Temple Gathering & Queue Corridor",
            "event_type": "temple",
            "description": "Pilgrims gathered in queue corridor before inner sanctum.",
            "file": "temple_crowd.jpg",
            "expected_density": "High Density"
        },
        {
            "id": "political-rally",
            "name": "Mega Political Rally Ground",
            "event_type": "political",
            "description": "High-density crowd assembled facing speaker podium.",
            "file": "political_rally.jpg",
            "expected_density": "Critical Density"
        },
        {
            "id": "cultural-festival",
            "name": "Cultural Street Festival & Fair",
            "event_type": "festival",
            "description": "Public procession and festive fair gathering.",
            "file": "cultural_festival.jpg",
            "expected_density": "Medium / High Density"
        },
        {
            "id": "public-celebration",
            "name": "Public City Celebration",
            "event_type": "celebration",
            "description": "Public assembly at outdoor celebration grounds.",
            "file": "public_celebration.jpg",
            "expected_density": "Normal / Moderate Crowd"
        }
    ]
    return {"samples": samples}


@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    event_type: str = Form("other"),
    privacy_mode: bool = Form(True),
    conf_threshold: float = Form(0.25),
    custom_low: Optional[int] = Form(None),
    custom_medium: Optional[int] = Form(None),
    custom_high: Optional[int] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Analyzes an uploaded image file:
    - Runs person detection (YOLOv8)
    - Computes crowd count
    - Classifies density level
    - Generates early warning alert & SOPs
    - Produces bounding box annotations & density heatmap
    - Saves event record into database history
    """
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        # Decode image to inspect shape
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")

        h, w = img_bgr.shape[:2]
        boxes, elapsed_ms = detect_people(
            img_bgr, conf_threshold=conf_threshold, enable_privacy_blur=privacy_mode
        )
        count = len(boxes)

        # Thresholds
        custom_thresh = None
        if custom_low is not None and custom_medium is not None and custom_high is not None:
            custom_thresh = {"low": custom_low, "medium": custom_medium, "high": custom_high}

        # Area ratio
        total_box_area = sum((b["x2"] - b["x1"]) * (b["y2"] - b["y1"]) for b in boxes)
        boxes_area_ratio = total_box_area / max(h * w, 1)

        # Classify density
        density_label, level_key, occupancy_pct, details = classify_crowd_density(
            count=count,
            event_type=event_type,
            custom_thresholds=custom_thresh,
            image_area=float(h * w),
            boxes_area_ratio=boxes_area_ratio
        )

        # Generate alert
        alert = generate_crowd_alert(level_key=level_key, event_type=event_type, count=count)

        # Render visual outputs
        annotated_bgr = render_annotated_image(
            img_bgr, boxes, density_level_key=level_key, enable_privacy_blur=privacy_mode
        )
        heatmap_bgr = generate_density_heatmap(img_bgr, boxes)

        annotated_b64 = encode_image_base64(annotated_bgr)
        heatmap_b64 = encode_image_base64(heatmap_bgr)

        # Save to database
        db_record = {
            "source_type": "image",
            "source_name": file.filename or "uploaded_image.jpg",
            "event_type": event_type,
            "event_name": details.get("event_name", "Public Gathering"),
            "crowd_count": count,
            "density_level": density_label,
            "level_key": level_key,
            "occupancy_pct": occupancy_pct,
            "alert_title": alert["title"],
            "alert_severity": alert["severity"],
            "processing_time_ms": elapsed_ms,
            "boxes": boxes,
            "image_w": w,
            "image_h": h
        }
        record_id = save_detection_record(db_record)

        if session_id:
            save_time_series_point(session_id, count, density_label, event_type)

        return {
            "record_id": record_id,
            "count": count,
            "density_label": density_label,
            "level_key": level_key,
            "occupancy_pct": occupancy_pct,
            "alert": alert,
            "event_type": event_type,
            "event_name": details.get("event_name"),
            "processing_time_ms": elapsed_ms,
            "width": w,
            "height": h,
            "boxes_count": len(boxes),
            "annotated_image": annotated_b64,
            "heatmap_image": heatmap_b64,
            "details": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-frame")
async def analyze_live_frame(payload: LiveFramePayload):
    """
    Lightweight, optimized endpoint for live webcam streaming frames.
    Accepts base64 encoded frame, returns count, density status, alert, and annotated image.
    """
    try:
        # Strip header if present
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]

        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid frame")

        h, w = img_bgr.shape[:2]
        boxes, elapsed_ms = detect_people(
            img_bgr, conf_threshold=payload.conf_threshold, enable_privacy_blur=payload.privacy_mode, imgsz=640
        )
        count = len(boxes)

        custom_thresh = None
        if payload.custom_low and payload.custom_medium and payload.custom_high:
            custom_thresh = {
                "low": payload.custom_low,
                "medium": payload.custom_medium,
                "high": payload.custom_high
            }

        density_label, level_key, occupancy_pct, details = classify_crowd_density(
            count=count,
            event_type=payload.event_type,
            custom_thresholds=custom_thresh
        )

        alert = generate_crowd_alert(level_key=level_key, event_type=payload.event_type, count=count)

        annotated_bgr = render_annotated_image(
            img_bgr, boxes, density_level_key=level_key, enable_privacy_blur=payload.privacy_mode
        )
        annotated_b64 = encode_image_base64(annotated_bgr, quality=75)

        # Log to time series if session_id is active
        if payload.session_id:
            save_time_series_point(payload.session_id, count, density_label, payload.event_type)

        return {
            "count": count,
            "density_label": density_label,
            "level_key": level_key,
            "occupancy_pct": occupancy_pct,
            "alert": alert,
            "boxes": boxes,
            "processing_time_ms": elapsed_ms,
            "annotated_image": annotated_b64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-video")
async def analyze_video(
    file: UploadFile = File(...),
    event_type: str = Form("other"),
    privacy_mode: bool = Form(True),
    conf_threshold: float = Form(0.25),
    sample_interval_sec: float = Form(1.0)
):
    """
    Analyzes an uploaded video file:
    - Samples frames periodically (e.g. every 1 second)
    - Tracks crowd count progression over video duration
    - Calculates peak count, average count, and risk timeline
    - Returns timeline series and keyframe snapshot
    """
    temp_video_path = os.path.join(STATIC_DIR, f"temp_{uuid.uuid4().hex}_{file.filename}")
    try:
        content = await file.read()
        with open(temp_video_path, "wb") as f:
            f.write(content)

        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_step = max(1, int(fps * sample_interval_sec))

        timeline = []
        max_count = 0
        peak_frame_b64 = None
        current_frame_idx = 0
        session_id = uuid.uuid4().hex[:8]

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if current_frame_idx % frame_step == 0:
                timestamp_sec = round(current_frame_idx / fps, 1)
                boxes, _ = detect_people(frame, conf_threshold=conf_threshold, enable_privacy_blur=privacy_mode)
                count = len(boxes)

                density_label, level_key, occupancy_pct, _ = classify_crowd_density(
                    count=count, event_type=event_type
                )

                if count >= max_count:
                    max_count = count
                    annotated_bgr = render_annotated_image(
                        frame, boxes, density_level_key=level_key, enable_privacy_blur=privacy_mode
                    )
                    peak_frame_b64 = encode_image_base64(annotated_bgr)

                timeline.append({
                    "time_sec": timestamp_sec,
                    "count": count,
                    "density_label": density_label,
                    "level_key": level_key
                })
                save_time_series_point(session_id, count, density_label, event_type)

            current_frame_idx += 1
            # Safeguard limit to avoid taking too long in college demo
            if len(timeline) >= 60:
                break

        cap.release()

        avg_count = round(sum(t["count"] for t in timeline) / max(len(timeline), 1), 1)
        final_density, final_level_key, _, _ = classify_crowd_density(max_count, event_type)
        alert = generate_crowd_alert(level_key=final_level_key, event_type=event_type, count=max_count)

        # Save peak detection record
        db_record = {
            "source_type": "video",
            "source_name": file.filename,
            "event_type": event_type,
            "event_name": EVENT_PRESETS.get(event_type, {}).get("name", "Public Gathering"),
            "crowd_count": max_count,
            "density_level": final_density,
            "level_key": final_level_key,
            "occupancy_pct": 0.0,
            "alert_title": alert["title"],
            "alert_severity": alert["severity"],
            "processing_time_ms": 0.0
        }
        save_detection_record(db_record)

        return {
            "video_name": file.filename,
            "total_samples": len(timeline),
            "peak_count": max_count,
            "avg_count": avg_count,
            "peak_density": final_density,
            "peak_level_key": final_level_key,
            "alert": alert,
            "timeline": timeline,
            "peak_annotated_image": peak_frame_b64
        }
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except Exception:
                pass


@app.post("/api/analyze-sample/{sample_id}")
async def analyze_sample(sample_id: str, privacy_mode: bool = True):
    """Analyze one of the preloaded demo samples."""
    mapping = {
        "temple-gathering": ("temple_crowd.jpg", "temple"),
        "political-rally": ("political_rally.jpg", "political"),
        "cultural-festival": ("cultural_festival.jpg", "festival"),
        "public-celebration": ("public_celebration.jpg", "celebration")
    }

    if sample_id not in mapping:
        raise HTTPException(status_code=404, detail="Sample preset not found.")

    filename, event_type = mapping[sample_id]
    sample_path = os.path.join(SAMPLES_DIR, filename)

    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail=f"Sample file {filename} not found.")

    with open(sample_path, "rb") as f:
        image_bytes = f.read()

    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img_bgr.shape[:2]

    boxes, elapsed_ms = detect_people(img_bgr, conf_threshold=0.25, enable_privacy_blur=privacy_mode)
    count = len(boxes)

    total_box_area = sum((b["x2"] - b["x1"]) * (b["y2"] - b["y1"]) for b in boxes)
    boxes_area_ratio = total_box_area / max(h * w, 1)

    density_label, level_key, occupancy_pct, details = classify_crowd_density(
        count=count, event_type=event_type, boxes_area_ratio=boxes_area_ratio
    )

    alert = generate_crowd_alert(level_key=level_key, event_type=event_type, count=count)

    annotated_bgr = render_annotated_image(
        img_bgr, boxes, density_level_key=level_key, enable_privacy_blur=privacy_mode
    )
    heatmap_bgr = generate_density_heatmap(img_bgr, boxes)

    annotated_b64 = encode_image_base64(annotated_bgr)
    heatmap_b64 = encode_image_base64(heatmap_bgr)

    # Save to DB
    db_record = {
        "source_type": "demo",
        "source_name": filename,
        "event_type": event_type,
        "event_name": details.get("event_name"),
        "crowd_count": count,
        "density_level": density_label,
        "level_key": level_key,
        "occupancy_pct": occupancy_pct,
        "alert_title": alert["title"],
        "alert_severity": alert["severity"],
        "processing_time_ms": elapsed_ms,
        "boxes": boxes,
        "image_w": w,
        "image_h": h
    }
    record_id = save_detection_record(db_record)

    return {
        "record_id": record_id,
        "count": count,
        "density_label": density_label,
        "level_key": level_key,
        "occupancy_pct": occupancy_pct,
        "alert": alert,
        "event_type": event_type,
        "event_name": details.get("event_name"),
        "processing_time_ms": elapsed_ms,
        "width": w,
        "height": h,
        "boxes_count": len(boxes),
        "annotated_image": annotated_b64,
        "heatmap_image": heatmap_b64,
        "details": details
    }


@app.get("/api/history")
def get_history(limit: int = 50, event_type: Optional[str] = None):
    return {"history": get_detection_history(limit=limit, event_type=event_type)}


@app.delete("/api/history")
def clear_detection_history():
    clear_history()
    return {"message": "Detection history cleared successfully."}


@app.get("/api/analytics")
def get_analytics():
    return get_analytics_summary()


# Mount static files
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

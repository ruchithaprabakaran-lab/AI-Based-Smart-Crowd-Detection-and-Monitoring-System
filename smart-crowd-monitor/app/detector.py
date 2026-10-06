"""
AI Crowd Detection Engine
Uses YOLOv8 for real-time person detection, crowd counting,
density heatmap generation, and privacy-preserving anonymization.
"""

import time
import base64
import os
import cv2
import numpy as np
from PIL import Image
import io
from typing import Dict, Any, List, Tuple, Optional

# Global cache for the YOLO model
_YOLO_MODEL = None
_MODEL_LOAD_FAILED = False


def get_yolo_model():
    """Lazy-load the YOLOv8 model."""
    global _YOLO_MODEL, _MODEL_LOAD_FAILED
    if _YOLO_MODEL is None and not _MODEL_LOAD_FAILED:
        try:
            from ultralytics import YOLO
            # Lightweight YOLOv8 nano model (fastest inference, accurate person detection)
            model_path = os.path.join(os.path.dirname(__file__), "yolov8n.pt")
            _YOLO_MODEL = YOLO(model_path if os.path.exists(model_path) else "yolov8n.pt")
        except Exception as e:
            print(f"[Detector] Warning: Could not load Ultralytics YOLO: {e}. Falling back to OpenCV detector.")
            _MODEL_LOAD_FAILED = True
    return _YOLO_MODEL


def detect_people_opencv_fallback(image_bgr: np.ndarray, conf_thresh: float = 0.3) -> List[Dict[str, Any]]:
    """Fallback detector using OpenCV HOG Person Detector if YOLO is unavailable."""
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Resize for faster processing if image is huge
    h, w = image_bgr.shape[:2]
    scale = 1.0
    if max(h, w) > 1000:
        scale = 1000.0 / max(h, w)
        resized = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))
    else:
        resized = image_bgr
        
    rects, weights = hog.detectMultiScale(resized, winStride=(4, 4), padding=(8, 8), scale=1.05)
    
    boxes = []
    for (rx, ry, rw, rh), weight in zip(rects, weights):
        if weight >= conf_thresh:
            x1 = int(rx / scale)
            y1 = int(ry / scale)
            x2 = int((rx + rw) / scale)
            y2 = int((ry + rh) / scale)
            boxes.append({
                "x1": max(0, x1),
                "y1": max(0, y1),
                "x2": min(w, x2),
                "y2": min(h, y2),
                "confidence": round(float(weight), 2),
                "label": "Person"
            })
    return boxes


def detect_people(
    image_bgr: np.ndarray,
    conf_threshold: float = 0.20,
    enable_privacy_blur: bool = False,
    imgsz: int = 1024
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Detect people in the image.
    Strictly detects persons (class 0). Privacy-safe: No facial recognition or identity tracking.
    """
    start_time = time.time()
    boxes = []
    model = get_yolo_model()
    
    if model is not None:
        try:
            # Run inference targeting only class 0 (person)
            results = model(image_bgr, classes=[0], conf=conf_threshold, imgsz=imgsz, verbose=False)
            if results and len(results) > 0:
                result = results[0]
                for box in result.boxes:
                    coords = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    boxes.append({
                        "x1": int(coords[0]),
                        "y1": int(coords[1]),
                        "x2": int(coords[2]),
                        "y2": int(coords[3]),
                        "confidence": round(conf, 2),
                        "label": "Person"
                    })
        except Exception as e:
            print(f"[Detector] YOLO inference error: {e}, falling back to OpenCV HOG")
            boxes = detect_people_opencv_fallback(image_bgr, conf_thresh=0.2)
    else:
        boxes = detect_people_opencv_fallback(image_bgr, conf_thresh=0.2)

    elapsed_ms = round((time.time() - start_time) * 1000, 1)
    return boxes, elapsed_ms


def generate_density_heatmap(image_bgr: np.ndarray, boxes: List[Dict[str, Any]]) -> np.ndarray:
    """
    Generate smooth Gaussian crowd density heatmap overlaid on the original image.
    """
    h, w = image_bgr.shape[:2]
    density_map = np.zeros((h, w), dtype=np.float32)
    
    if not boxes:
        return image_bgr.copy()
        
    for box in boxes:
        cx = int((box["x1"] + box["x2"]) / 2)
        cy = int((box["y1"] + box["y2"]) / 2)
        bw = max(10, box["x2"] - box["x1"])
        bh = max(10, box["y2"] - box["y1"])
        
        # Kernel radius proportional to person bounding box size
        radius = int(max(bw, bh) * 0.75)
        radius = max(15, min(radius, 120))
        
        # Add circular/Gaussian accumulation
        cv2.circle(density_map, (cx, cy), radius, 1.0, -1)
        
    # Smooth the accumulation map
    density_map = cv2.GaussianBlur(density_map, (61, 61), 0)
    
    # Normalize to 0-255
    max_val = np.max(density_map)
    if max_val > 0:
        norm_map = (density_map / max_val * 255).astype(np.uint8)
    else:
        norm_map = np.zeros((h, w), dtype=np.uint8)
        
    # Colorize using JET or TURBO colormap
    heatmap_color = cv2.applyColorMap(norm_map, cv2.COLORMAP_JET)
    
    # Blend with original frame (0.55 image, 0.45 heatmap)
    blended = cv2.addWeighted(image_bgr, 0.55, heatmap_color, 0.45, 0)
    return blended


def render_annotated_image(
    image_bgr: np.ndarray,
    boxes: List[Dict[str, Any]],
    density_level_key: str = "low",
    enable_privacy_blur: bool = True
) -> np.ndarray:
    """
    Draw clean, high-visibility bounding boxes, counters, and optional privacy blur.
    """
    output = image_bgr.copy()
    h, w = output.shape[:2]

    # Color scheme according to crowd severity level
    palette = {
        "low": (16, 185, 129),       # #10b981 (BGR: 129, 185, 16)
        "medium": (11, 158, 245),    # #f59e0b (BGR: 11, 158, 245)
        "high": (22, 115, 249),      # #f97316 (BGR: 22, 115, 249)
        "critical": (68, 68, 239)    # #ef4444 (BGR: 68, 68, 239)
    }
    box_color = palette.get(density_level_key, (129, 185, 16))

    for idx, box in enumerate(boxes, 1):
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
        bw = x2 - x1
        bh = y2 - y1

        # 1. Privacy Protection: Anonymize face/head region by blurring upper 25% of detection
        if enable_privacy_blur and bh > 15 and bw > 15:
            head_y2 = min(y1 + int(bh * 0.28), y2)
            head_roi = output[y1:head_y2, x1:x2]
            if head_roi.size > 0:
                k_size = max(15, (bw // 4) * 2 + 1)
                blurred_roi = cv2.GaussianBlur(head_roi, (k_size, k_size), 30)
                output[y1:head_y2, x1:x2] = blurred_roi

        # 2. Modern sleek bounding box (Corner highlights or clean rectangle)
        cv2.rectangle(output, (x1, y1), (x2, y2), box_color, 2)
        
        # Draw corner accents for high-tech HUD look
        line_len = min(15, bw // 3, bh // 3)
        if line_len > 4:
            # Top-left
            cv2.line(output, (x1, y1), (x1 + line_len, y1), (255, 255, 255), 3)
            cv2.line(output, (x1, y1), (x1, y1 + line_len), (255, 255, 255), 3)
            # Bottom-right
            cv2.line(output, (x2, y2), (x2 - line_len, y2), (255, 255, 255), 3)
            cv2.line(output, (x2, y2), (x2, y2 - line_len), (255, 255, 255), 3)

        # 3. Label tag (e.g., #1, #2)
        tag_text = f"#{idx} ({int(box['confidence']*100)}%)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.4
        thickness = 1
        (tw, th), _ = cv2.getTextSize(tag_text, font, scale, thickness)
        
        # Tag background
        tag_y1 = max(0, y1 - th - 6)
        cv2.rectangle(output, (x1, tag_y1), (x1 + tw + 6, tag_y1 + th + 6), box_color, -1)
        cv2.putText(output, tag_text, (x1 + 3, tag_y1 + th + 2), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    # Add overlay watermark / status summary bar at top
    bar_h = 36
    overlay = output.copy()
    cv2.rectangle(overlay, (0, 0), (w, bar_h), (20, 24, 33), -1)
    cv2.addWeighted(overlay, 0.75, output, 0.25, 0, output)
    
    cv2.putText(
        output,
        f"Smart Crowd AI | Count: {len(boxes)} Persons | Privacy Preserving [No Biometrics]",
        (12, 23),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return output


def encode_image_base64(image_bgr: np.ndarray, quality: int = 85) -> str:
    """Encode OpenCV BGR image to JPEG Base64 string."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode('.jpg', image_bgr, encode_param)
    if not success:
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')


def process_image_bytes(
    image_bytes: bytes,
    conf_threshold: float = 0.25,
    enable_privacy_blur: bool = True,
    density_level_key: str = "low"
) -> Dict[str, Any]:
    """
    Main pipeline to process raw image bytes.
    Returns counts, bounding boxes, annotated image, and heatmap base64 strings.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("Invalid image file or unsupported image format.")

    h, w = image_bgr.shape[:2]
    boxes, elapsed_ms = detect_people(image_bgr, conf_threshold=conf_threshold, enable_privacy_blur=enable_privacy_blur)

    # Calculate total bounding box area ratio
    total_box_area = sum((b["x2"] - b["x1"]) * (b["y2"] - b["y1"]) for b in boxes)
    total_img_area = h * w
    box_area_ratio = total_box_area / max(total_img_area, 1)

    # Render visualizations
    annotated_bgr = render_annotated_image(
        image_bgr, boxes, density_level_key=density_level_key, enable_privacy_blur=enable_privacy_blur
    )
    heatmap_bgr = generate_density_heatmap(image_bgr, boxes)

    return {
        "count": len(boxes),
        "boxes": boxes,
        "width": w,
        "height": h,
        "processing_time_ms": elapsed_ms,
        "box_area_ratio": box_area_ratio,
        "annotated_image": encode_image_base64(annotated_bgr),
        "heatmap_image": encode_image_base64(heatmap_bgr)
    }

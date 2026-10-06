"""
Crowd Density Classification Module
Handles density estimation, thresholds per gathering type, and occupancy ratios.
"""

from typing import Dict, Any, Tuple

# Pre-defined threshold presets for various gathering scenarios
EVENT_PRESETS: Dict[str, Dict[str, Any]] = {
    "temple": {
        "name": "Temple Gathering & Religious Event",
        "description": "Inner sanctums, darshan queues, choke points, and narrow temple corridors.",
        "thresholds": {"low": 5, "medium": 10, "high": 15},  # > 15 is Critical
        "risk_factors": ["Narrow corridors", "Queue bottlenecks", "Barricade pressure"]
    },
    "political": {
        "name": "Political Rally & Public Meeting",
        "description": "Large grounds, speaker podium front-zones, and open rallies.",
        "thresholds": {"low": 8, "medium": 16, "high": 24},  # > 24 is Critical
        "risk_factors": ["Podium surge", "Entry/exit gate congestions", "Perimeter boundary rushes"]
    },
    "festival": {
        "name": "Festival & Cultural Event",
        "description": "Fairgrounds, street processions, immersion points, and cultural festivities.",
        "thresholds": {"low": 6, "medium": 12, "high": 18},  # > 18 is Critical
        "risk_factors": ["Procession halts", "Vendor stall blockages", "Two-way crowd collision"]
    },
    "celebration": {
        "name": "Public Celebration",
        "description": "City plazas, fireworks vantage points, and public celebrations.",
        "thresholds": {"low": 8, "medium": 16, "high": 25},
        "risk_factors": ["Vantage point crowding", "Dispersal rushes", "Transit hub convergence"]
    },
    "meeting": {
        "name": "Large Meeting & Function",
        "description": "Auditoriums, convention halls, banquet spaces, and indoor conferences.",
        "thresholds": {"low": 5, "medium": 12, "high": 20},
        "risk_factors": ["Doorway clogs", "Seating aisle congestion", "Fire-exit obstruction"]
    },
    "other": {
        "name": "Other Public Gathering",
        "description": "General purpose monitoring for public areas, transit spots, and markets.",
        "thresholds": {"low": 6, "medium": 14, "high": 22},
        "risk_factors": ["Pedestrian density spike", "Stationary loitering", "Corridor blockage"]
    }
}


def classify_crowd_density(
    count: int,
    event_type: str = "other",
    custom_thresholds: Dict[str, int] = None,
    image_area: float = None,
    boxes_area_ratio: float = None
) -> Tuple[str, str, float, Dict[str, Any]]:
    """
    Classify crowd into:
      - Low Density
      - Medium Density
      - High Density
      - Critical Density
    
    Returns:
      (density_level, level_key, occupancy_percent, details)
    """
    event_cfg = EVENT_PRESETS.get(event_type, EVENT_PRESETS["other"])
    thresholds = custom_thresholds or event_cfg["thresholds"]
    
    low_max = thresholds.get("low", 25)
    med_max = thresholds.get("medium", 60)
    high_max = thresholds.get("high", 100)
    
    # Calculate approximate occupancy percentage relative to high threshold
    # 100% represents the boundary between High and Critical
    occupancy_pct = round((count / max(high_max, 1)) * 100, 1)

    if count <= low_max:
        level_key = "low"
        density_label = "Low Density"
        color = "#10b981"  # Emerald green
        badge_class = "density-low"
    elif count <= med_max:
        level_key = "medium"
        density_label = "Medium Density"
        color = "#f59e0b"  # Amber yellow
        badge_class = "density-medium"
    elif count <= high_max:
        level_key = "high"
        density_label = "High Density"
        color = "#f97316"  # Orange
        badge_class = "density-high"
    else:
        level_key = "critical"
        density_label = "Critical Density"
        color = "#ef4444"  # Red
        badge_class = "density-critical"

    details = {
        "event_type": event_type,
        "event_name": event_cfg["name"],
        "thresholds": thresholds,
        "occupancy_pct": occupancy_pct,
        "color": color,
        "badge_class": badge_class,
        "boxes_area_ratio": round(boxes_area_ratio * 100, 2) if boxes_area_ratio is not None else None
    }

    return density_label, level_key, occupancy_pct, details

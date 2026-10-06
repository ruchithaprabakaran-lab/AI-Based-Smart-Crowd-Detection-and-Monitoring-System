"""
Early Warning and Alert System for Smart Crowd Monitoring.
Generates human-understandable warnings, severity codes, and actionable SOP recommendations.
"""

from typing import Dict, Any, List

ALERT_RULES: Dict[str, Dict[str, Any]] = {
    "low": {
        "title": "Normal Crowd",
        "severity": "normal",
        "icon": "shield-check",
        "color": "#10b981",
        "sound": None,
        "urgency": "Low Risk",
        "summary": "Crowd density is within safe operational limits. Movement is unhindered.",
        "sops": [
            "Maintain standard entrance flow and routine volunteer patrols.",
            "Keep all automated crowd monitoring sensors online.",
            "Record baseline crowd influx for temporal comparison."
        ]
    },
    "medium": {
        "title": "Crowd Increasing",
        "severity": "advisory",
        "icon": "users-round",
        "color": "#f59e0b",
        "sound": "notice",
        "urgency": "Moderate Caution",
        "summary": "Crowd density is climbing steadily. Density approaching cautionary buffer zone.",
        "sops": [
            "Alert security marshals and ground staff to monitor choke points.",
            "Regulate batch entry at ticket / checkpoint barriers.",
            "Ensure passage corridors and pathways remain clear of stationary crowds."
        ]
    },
    "high": {
        "title": "High Crowd Density - Attention Required",
        "severity": "warning",
        "icon": "alert-triangle",
        "color": "#f97316",
        "sound": "warning",
        "urgency": "High Alert",
        "summary": "Density is high. Pedestrian spacing is restricted, risk of bottlenecking detected.",
        "sops": [
            "Activate secondary holding areas and prepare diversion routes.",
            "Slow down incoming queue admissions by 50%.",
            "Make public address announcements to guide crowd flow steadily.",
            "Deploy quick-response ground teams to high-density zones."
        ]
    },
    "critical": {
        "title": "Critical Crowd Density - Immediate Attention Required",
        "severity": "critical",
        "icon": "siren",
        "color": "#ef4444",
        "sound": "emergency",
        "urgency": "Emergency Intervention",
        "summary": "Dangerous crowd compression detected! Immediate intervention required to prevent crush hazard.",
        "sops": [
            "IMMEDIATELY halt all incoming entries into the monitored sector.",
            "Open emergency exit corridors, side gates, and perimeter dispersal pathways.",
            "Initiate emergency crowd dispersal and sound directional guidance over PA systems.",
            "Dispatch emergency crowd control marshals and medical first responders to congested sectors."
        ]
    }
}


# Tailored event-specific tips to enhance the college demo & real-world utility
EVENT_SPECIFIC_SOPS: Dict[str, Dict[str, List[str]]] = {
    "temple": {
        "high": ["Hold pilgrims in queue sheds before inner sanctum.", "Ensure free movement in narrow pradakshina paths."],
        "critical": ["Immediate release into outer prakaram gardens.", "Halt queue token scanning temporarily."]
    },
    "political": {
        "high": ["Reinforce front barricades near speaker podium.", "Activate side egress exits."],
        "critical": ["Direct crowd into open perimeter sectors.", "Pause podium program if barricade surge occurs."]
    },
    "festival": {
        "high": ["Clear food stalls and vendor carts away from core parade path.", "Enforce one-way walking lane."],
        "critical": ["Hold procession floats until intersection choke points clear.", "Open perimeter boundary exits."]
    },
    "celebration": {
        "high": ["Direct late arrivals to secondary viewing screens.", "Keep metro/transit access ways fluid."],
        "critical": ["Broadcast transit departure staggered schedules.", "Clear primary plaza convergence points."]
    },
    "meeting": {
        "high": ["Direct attendees to balcony and auxiliary seating wings.", "Keep double doors propped open."],
        "critical": ["Halt hall admission; divert to live overflow broadcast hall.", "Keep all exit fire doors clear."]
    },
    "other": {
        "high": ["Direct security to disperse lingering clusters.", "Maintain continuous surveillance."],
        "critical": ["Implement rapid sector clearance.", "Contact facility emergency response."]
    }
}


def generate_crowd_alert(level_key: str, event_type: str = "other", count: int = 0) -> Dict[str, Any]:
    """
    Generate complete alert payload for the UI.
    """
    base_alert = ALERT_RULES.get(level_key, ALERT_RULES["low"]).copy()
    
    # Merge event specific SOPs if available for high/critical levels
    specific = EVENT_SPECIFIC_SOPS.get(event_type, {}).get(level_key, [])
    combined_sops = base_alert["sops"].copy()
    if specific:
        combined_sops = specific + combined_sops
        
    return {
        "title": base_alert["title"],
        "severity": base_alert["severity"],
        "level_key": level_key,
        "icon": base_alert["icon"],
        "color": base_alert["color"],
        "sound": base_alert["sound"],
        "urgency": base_alert["urgency"],
        "summary": base_alert["summary"],
        "sops": combined_sops,
        "crowd_count": count,
        "timestamp_iso": None  # populated at runtime
    }

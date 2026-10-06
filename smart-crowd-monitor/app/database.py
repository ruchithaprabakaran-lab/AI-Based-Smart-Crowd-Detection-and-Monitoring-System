"""
SQLite Database Module for Crowd Detection History & Time-Series Analytics
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "crowd_monitoring.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_type TEXT NOT NULL, -- 'image', 'video', 'webcam', 'demo'
                source_name TEXT,
                event_type TEXT NOT NULL,
                event_name TEXT,
                crowd_count INTEGER NOT NULL,
                density_level TEXT NOT NULL,
                level_key TEXT NOT NULL,
                occupancy_pct REAL,
                alert_title TEXT NOT NULL,
                alert_severity TEXT NOT NULL,
                processing_time_ms REAL,
                boxes_json TEXT,
                image_w INTEGER,
                image_h INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_series_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                crowd_count INTEGER NOT NULL,
                density_level TEXT NOT NULL,
                event_type TEXT NOT NULL
            )
        """)
        conn.commit()


def save_detection_record(record: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = record.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        boxes_json = json.dumps(record.get("boxes", []))
        
        cursor.execute("""
            INSERT INTO detection_history (
                timestamp, source_type, source_name, event_type, event_name,
                crowd_count, density_level, level_key, occupancy_pct,
                alert_title, alert_severity, processing_time_ms,
                boxes_json, image_w, image_h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_str,
            record.get("source_type", "image"),
            record.get("source_name", "analysis"),
            record.get("event_type", "other"),
            record.get("event_name", "Public Gathering"),
            record.get("crowd_count", 0),
            record.get("density_level", "Low Density"),
            record.get("level_key", "low"),
            record.get("occupancy_pct", 0.0),
            record.get("alert_title", "Normal Crowd"),
            record.get("alert_severity", "normal"),
            record.get("processing_time_ms", 0.0),
            boxes_json,
            record.get("image_w", 0),
            record.get("image_h", 0)
        ))
        conn.commit()
        return cursor.lastrowid


def save_time_series_point(session_id: str, count: int, density_level: str, event_type: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%H:%M:%S")
        cursor.execute("""
            INSERT INTO time_series_points (session_id, timestamp, crowd_count, density_level, event_type)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, now_str, count, density_level, event_type))
        conn.commit()


def get_detection_history(limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if event_type and event_type != "all":
            cursor.execute("""
                SELECT * FROM detection_history 
                WHERE event_type = ? 
                ORDER BY id DESC LIMIT ?
            """, (event_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM detection_history 
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "source_type": r["source_type"],
                "source_name": r["source_name"],
                "event_type": r["event_type"],
                "event_name": r["event_name"],
                "crowd_count": r["crowd_count"],
                "density_level": r["density_level"],
                "level_key": r["level_key"],
                "occupancy_pct": r["occupancy_pct"],
                "alert_title": r["alert_title"],
                "alert_severity": r["alert_severity"],
                "processing_time_ms": r["processing_time_ms"]
            })
        return results


def get_analytics_summary() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total scans
        cursor.execute("SELECT COUNT(*), AVG(crowd_count), MAX(crowd_count), MIN(crowd_count) FROM detection_history")
        total_scans, avg_count, peak_count, min_count = cursor.fetchone()
        
        # Breakdown by density level
        cursor.execute("""
            SELECT level_key, COUNT(*) FROM detection_history GROUP BY level_key
        """)
        breakdown_rows = cursor.fetchall()
        breakdown = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for k, cnt in breakdown_rows:
            if k in breakdown:
                breakdown[k] = cnt
                
        # Recent scans for time series chart (last 20)
        cursor.execute("""
            SELECT id, timestamp, crowd_count, density_level, level_key 
            FROM detection_history 
            ORDER BY id ASC LIMIT 30
        """)
        timeline_rows = cursor.fetchall()
        timeline = [{
            "id": r["id"],
            "time": r["timestamp"].split(" ")[-1] if " " in r["timestamp"] else r["timestamp"],
            "count": r["crowd_count"],
            "density": r["density_level"],
            "level_key": r["level_key"]
        } for r in timeline_rows]
        
        return {
            "total_scans": total_scans or 0,
            "avg_count": round(avg_count or 0, 1),
            "peak_count": peak_count or 0,
            "min_count": min_count or 0,
            "density_breakdown": breakdown,
            "timeline": timeline
        }


def clear_history():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detection_history")
        cursor.execute("DELETE FROM time_series_points")
        conn.commit()

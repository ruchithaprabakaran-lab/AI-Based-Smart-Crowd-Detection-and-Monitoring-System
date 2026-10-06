# 🛡️ Smart Crowd Detection and Monitoring System (AI Ops)

An AI-powered, real-time web application engineered to monitor crowd density and provide early warnings in high-gathering public venues to prevent dangerous overcrowding and stampedes.

---

## 🌐 Quick Access Link

The application is running live at:
### 👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or [http://localhost:8000](http://localhost:8000))

---

## 🎯 Target Locations & Use Cases
- **Temple Gatherings & Religious Events:** Inner sanctum queues, darshan choke corridors, and narrow prakarams.
- **Political Party Meetings & Public Rallies:** Stage barricade sectors, speaker podium front-zones, and open rally grounds.
- **Festivals & Cultural Events:** Street processions, fairgrounds, and immersion bottlenecks.
- **Public Celebrations:** City plazas, fireworks vantage points, and transit interchange convergence.
- **Large Meetings & Indoor Functions:** Auditoriums, convention halls, and banquet spaces.
- **General Public Spaces:** Transit stations, pedestrian market streets, and choke corridors.

---

## 🚀 Key Features

1. **AI Computer Vision Person Detection (YOLOv8 + OpenCV)**
   - Powered by pre-trained Ultralytics YOLOv8 nano with automatic OpenCV fallback.
   - Accurately counts people in still images, video files, and real-time webcam streams.
   - Sub-150ms inference time on standard CPUs.

2. **Four-Tier Crowd Density Classification**
   - 🟢 **Low Density (Normal Crowd):** Safe pedestrian flow.
   - 🟡 **Medium Density (Crowd Increasing):** Advisory alert, buffer zone approached.
   - 🟠 **High Density (Attention Required):** Compression risk, bottlenecks forming.
   - 🔴 **Critical Density (Immediate Attention Required):** Dangerous crush hazard, immediate dispersal needed.

3. **Dual Visual Monitor (HUD)**
   - **Bounding Box Mode:** Neon corner-bracketed bounding boxes with individual person labels (`#1, #2...`) and confidence tags.
   - **Thermal Density Heatmap Mode:** Gaussian accumulation heatmap rendered over the original scene to spotlight congestion hotspots.

4. **Multi-Channel Alert System**
   - Pulsating visual warning banners (orange for High, flashing red for Critical).
   - Real-time audio alerts (warning chime & emergency dual-tone siren using Web Audio API synthesis).
   - Event-specific Standard Operating Procedures (SOPs) recommending actionable crowd control protocols to authorities.

5. **1-Click College Demo Presets**
   - Pre-loaded sample scenarios for Temple Queues, Political Rallies, Cultural Festivals, and City Celebrations—ideal for project evaluation without manual file preparation.

6. **Real-Time Analytics & Audit Trail**
   - Interactive Chart.js time-series graph tracking crowd dynamics over time.
   - Density distribution doughnut chart.
   - Persistent SQLite audit history log with CSV export capability.

7. **🔒 Privacy-Preserving Architecture (Safety by Design)**
   - Zero facial recognition or identity tracking.
   - No biometrics collected or stored.
   - Automatic head/face Gaussian blur anonymization toggle.

---

## 💻 Tech Stack
- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLite
- **Computer Vision:** Ultralytics YOLOv8, PyTorch, OpenCV, Pillow, NumPy
- **Frontend:** HTML5, Tailwind CSS, JavaScript (ES6+), Chart.js, Lucide Icons, Web Audio API

---

## 🛠️ How to Run Locally

### Method 1: Double-Click Launcher
- Double-click **`run.bat`** (Windows Batch) or run **`start.ps1`** (PowerShell).

### Method 2: Command Line
```powershell
cd C:\Users\ruchi\.gemini\antigravity\scratch\smart-crowd-monitor
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

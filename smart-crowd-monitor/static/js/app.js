/**
 * Smart Crowd Detection and Monitoring System
 * Modern Frontend Controller with Real-Time Vision & Audio Alerts
 */

// Application State
const state = {
  currentMode: 'image', // 'image', 'webcam', 'video', 'presets'
  currentView: 'annotated', // 'annotated', 'heatmap'
  eventType: 'temple',
  soundEnabled: true,
  privacyMode: true,
  confThreshold: 0.20,
  selectedImageFile: null,
  selectedVideoFile: null,
  webcamStream: null,
  webcamInterval: null,
  isAnalyzingWebcam: false,
  webcamLastFrameTime: 0,
  webcamFps: 0,
  sessionId: 'sess_' + Math.random().toString(36).substring(2, 9),
  lastAnalysis: null,
  trendChart: null,
  donutChart: null
};

// Web Audio API Sound Synthesizer for Alerts
const soundEngine = {
  ctx: null,
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  },
  playTone(freq, type = 'sine', duration = 0.2, gainVal = 0.15) {
    if (!state.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn('Audio play error:', e);
    }
  },
  playWarningChime() {
    // 2-tone cautionary chime
    this.playTone(440, 'triangle', 0.15, 0.2);
    setTimeout(() => this.playTone(554, 'triangle', 0.25, 0.2), 160);
  },
  playEmergencySiren() {
    // Emergency dual alert
    this.playTone(880, 'sawtooth', 0.2, 0.25);
    setTimeout(() => this.playTone(660, 'sawtooth', 0.2, 0.25), 200);
    setTimeout(() => this.playTone(880, 'sawtooth', 0.2, 0.25), 400);
  }
};

// DOM Element References
const elements = {
  // Tabs
  tabImage: document.getElementById('tab-image'),
  tabWebcam: document.getElementById('tab-webcam'),
  tabVideo: document.getElementById('tab-video'),
  tabPresets: document.getElementById('tab-presets'),
  containerImage: document.getElementById('mode-image-container'),
  containerWebcam: document.getElementById('mode-webcam-container'),
  containerVideo: document.getElementById('mode-video-container'),
  containerPresets: document.getElementById('mode-presets-container'),

  // Event config
  eventTypeSelect: document.getElementById('event-type-select'),
  eventDescHint: document.getElementById('event-desc-hint'),
  privacyToggle: document.getElementById('privacy-toggle'),
  confSlider: document.getElementById('conf-slider'),
  confVal: document.getElementById('conf-val'),

  // Image inputs
  dropzone: document.getElementById('dropzone'),
  imageFileInput: document.getElementById('image-file-input'),
  analyzeImageBtn: document.getElementById('analyze-image-btn'),

  // Video inputs
  videoDropzone: document.getElementById('video-dropzone'),
  videoFileInput: document.getElementById('video-file-input'),
  analyzeVideoBtn: document.getElementById('analyze-video-btn'),
  videoProgressWrap: document.getElementById('video-progress-wrap'),
  videoProgressText: document.getElementById('video-progress-text'),

  // Webcam inputs
  startCamBtn: document.getElementById('start-cam-btn'),
  stopCamBtn: document.getElementById('stop-cam-btn'),
  webcamVideo: document.getElementById('webcam-video'),
  webcamOverlayCanvas: document.getElementById('webcam-overlay-canvas'),
  camStatsBar: document.getElementById('cam-stats-bar'),
  camFpsBadge: document.getElementById('cam-fps-badge'),

  // Viewport
  viewportContainer: document.getElementById('viewport-container'),
  viewportPlaceholder: document.getElementById('viewport-placeholder'),
  annotatedResultImg: document.getElementById('annotated-result-img'),
  heatmapResultImg: document.getElementById('heatmap-result-img'),
  viewportLoader: document.getElementById('viewport-loader'),
  loaderMsg: document.getElementById('loader-msg'),
  viewportCountBadge: document.getElementById('viewport-count-badge'),
  hudStatus: document.getElementById('hud-status'),
  hudRes: document.getElementById('hud-res'),
  hudDensity: document.getElementById('hud-density'),
  inferenceTimeLabel: document.getElementById('inference-time-label'),
  downloadResultBtn: document.getElementById('download-result-btn'),
  viewAnnotatedBtn: document.getElementById('view-annotated-btn'),
  viewHeatmapBtn: document.getElementById('view-heatmap-btn'),

  // KPI cards
  kpiCount: document.getElementById('kpi-count'),
  kpiCountSub: document.getElementById('kpi-count-sub'),
  kpiDensityBadge: document.getElementById('kpi-density-badge'),
  kpiOccupancyBar: document.getElementById('kpi-occupancy-bar'),
  kpiEventName: document.getElementById('kpi-event-name'),
  kpiEventType: document.getElementById('kpi-event-type'),
  kpiThresholdText: document.getElementById('kpi-threshold-text'),
  kpiStatusText: document.getElementById('kpi-status-text'),
  kpiStatusUrgency: document.getElementById('kpi-status-urgency'),
  kpiLatency: document.getElementById('kpi-latency'),

  // Alert banner & SOPs
  alertBanner: document.getElementById('alert-banner'),
  alertBannerTitle: document.getElementById('alert-banner-title'),
  alertBannerDesc: document.getElementById('alert-banner-desc'),
  sopUrgencyBadge: document.getElementById('sop-urgency-badge'),
  sopSummary: document.getElementById('sop-summary'),
  sopList: document.getElementById('sop-list'),

  // Sound & Modals
  toggleSoundBtn: document.getElementById('toggle-sound-btn'),
  soundStatusText: document.getElementById('sound-status-text'),
  soundIcon: document.getElementById('sound-icon'),
  infoModalBtn: document.getElementById('info-modal-btn'),
  infoModal: document.getElementById('info-modal'),
  closeModalBtn: document.getElementById('close-modal-btn'),
  closeModalBottomBtn: document.getElementById('close-modal-bottom-btn'),

  // History table
  historyFilterSelect: document.getElementById('history-filter-select'),
  exportHistoryBtn: document.getElementById('export-history-btn'),
  clearHistoryBtn: document.getElementById('clear-history-btn'),
  historyTableBody: document.getElementById('history-table-body')
};

// Event Description Tooltips
const EVENT_HINTS = {
  temple: "Inner sanctums, darshan queues, choke points, and narrow temple corridors.",
  political: "Large open grounds, stage barricade front sectors, and podium surge areas.",
  festival: "Fairgrounds, street processions, vendor blockages, and cultural festivities.",
  celebration: "City plazas, fireworks vantage points, and public celebrations.",
  meeting: "Auditoriums, convention halls, banquet spaces, and indoor conferences.",
  other: "General public spaces, pedestrian walkways, transit stops, and markets."
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
  setupEventListeners();
  initCharts();
  loadAnalyticsSummary();
  loadDetectionHistory();
});

// Event Listeners Setup
function setupEventListeners() {
  // Mode Tabs
  elements.tabImage.addEventListener('click', () => switchMode('image'));
  elements.tabWebcam.addEventListener('click', () => switchMode('webcam'));
  elements.tabVideo.addEventListener('click', () => switchMode('video'));
  elements.tabPresets.addEventListener('click', () => switchMode('presets'));

  // Event Type Selector
  elements.eventTypeSelect.addEventListener('change', (e) => {
    state.eventType = e.target.value;
    elements.eventDescHint.textContent = EVENT_HINTS[state.eventType] || "";
    elements.kpiEventType.textContent = e.target.options[e.target.selectedIndex].text;
  });

  // Confidence slider
  elements.confSlider.addEventListener('input', (e) => {
    state.confThreshold = e.target.value / 100;
    elements.confVal.textContent = `${e.target.value}%`;
  });

  // Privacy toggle
  elements.privacyToggle.addEventListener('change', (e) => {
    state.privacyMode = e.target.checked;
  });

  // Sound toggle
  elements.toggleSoundBtn.addEventListener('click', () => {
    state.soundEnabled = !state.soundEnabled;
    elements.soundStatusText.textContent = state.soundEnabled ? 'ON' : 'OFF';
    elements.soundStatusText.className = state.soundEnabled ? 'text-emerald-400' : 'text-slate-400';
    if (state.soundEnabled) soundEngine.playTone(600, 'sine', 0.1);
  });

  // Viewport switchers (Annotated vs Heatmap)
  elements.viewAnnotatedBtn.addEventListener('click', () => switchView('annotated'));
  elements.viewHeatmapBtn.addEventListener('click', () => switchView('heatmap'));

  // Dropzone file handling (Image)
  elements.dropzone.addEventListener('click', () => elements.imageFileInput.click());
  elements.imageFileInput.addEventListener('change', (e) => handleImageSelect(e.target.files[0]));

  elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('border-blue-500', 'bg-blue-500/5');
  });
  elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('border-blue-500', 'bg-blue-500/5');
  });
  elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('border-blue-500', 'bg-blue-500/5');
    if (e.dataTransfer.files.length > 0) {
      handleImageSelect(e.dataTransfer.files[0]);
    }
  });

  // Analyze Image Button
  elements.analyzeImageBtn.addEventListener('click', runImageAnalysis);

  // Video Dropzone file handling
  elements.videoDropzone.addEventListener('click', () => elements.videoFileInput.click());
  elements.videoFileInput.addEventListener('change', (e) => handleVideoSelect(e.target.files[0]));
  elements.analyzeVideoBtn.addEventListener('click', runVideoAnalysis);

  // Preset Buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sampleId = btn.getAttribute('data-sample');
      const eventType = btn.getAttribute('data-type');
      if (eventType) {
        state.eventType = eventType;
        elements.eventTypeSelect.value = eventType;
        elements.eventDescHint.textContent = EVENT_HINTS[eventType] || "";
      }
      runSampleAnalysis(sampleId);
    });
  });

  // Webcam Controls
  elements.startCamBtn.addEventListener('click', startWebcam);
  elements.stopCamBtn.addEventListener('click', stopWebcam);

  // Download Frame
  elements.downloadResultBtn.addEventListener('click', downloadCurrentResult);

  // Info Modal
  elements.infoModalBtn.addEventListener('click', () => elements.infoModal.classList.remove('hidden'));
  elements.closeModalBtn.addEventListener('click', () => elements.infoModal.classList.add('hidden'));
  elements.closeModalBottomBtn.addEventListener('click', () => elements.infoModal.classList.add('hidden'));

  // History Actions
  elements.historyFilterSelect.addEventListener('change', (e) => loadDetectionHistory(e.target.value));
  elements.exportHistoryBtn.addEventListener('click', exportHistoryCSV);
  elements.clearHistoryBtn.addEventListener('click', clearHistory);
}

// Mode Switcher
function switchMode(mode) {
  state.currentMode = mode;
  const tabBtns = [elements.tabImage, elements.tabWebcam, elements.tabVideo, elements.tabPresets];
  const containers = [elements.containerImage, elements.containerWebcam, elements.containerVideo, elements.containerPresets];

  tabBtns.forEach(b => b.classList.remove('active'));
  containers.forEach(c => c.classList.add('hidden'));

  if (mode === 'image') {
    elements.tabImage.classList.add('active');
    elements.containerImage.classList.remove('hidden');
    if (state.isAnalyzingWebcam) stopWebcam();
  } else if (mode === 'webcam') {
    elements.tabWebcam.classList.add('active');
    elements.containerWebcam.classList.remove('hidden');
  } else if (mode === 'video') {
    elements.tabVideo.classList.add('active');
    elements.containerVideo.classList.remove('hidden');
    if (state.isAnalyzingWebcam) stopWebcam();
  } else if (mode === 'presets') {
    elements.tabPresets.classList.add('active');
    elements.containerPresets.classList.remove('hidden');
    if (state.isAnalyzingWebcam) stopWebcam();
  }
}

// View Switcher (Bounding Boxes vs Heatmap)
function switchView(view) {
  state.currentView = view;
  elements.viewAnnotatedBtn.classList.toggle('active', view === 'annotated');
  elements.viewHeatmapBtn.classList.toggle('active', view === 'heatmap');

  if (state.lastAnalysis) {
    if (view === 'annotated') {
      elements.annotatedResultImg.classList.remove('hidden');
      elements.heatmapResultImg.classList.add('hidden');
    } else {
      elements.annotatedResultImg.classList.add('hidden');
      elements.heatmapResultImg.classList.remove('hidden');
    }
  }
}

// Handle Image File Selection
function handleImageSelect(file) {
  if (!file) return;
  state.selectedImageFile = file;
  elements.analyzeImageBtn.disabled = false;
  elements.dropzone.querySelector('p.text-xs').textContent = `Selected: ${file.name}`;
  elements.dropzone.querySelector('p.text-[10px]').textContent = `${(file.size / 1024).toFixed(1)} KB`;

  // Quick preview in viewport
  const reader = new FileReader();
  reader.onload = (e) => {
    elements.viewportPlaceholder.classList.add('hidden');
    elements.annotatedResultImg.src = e.target.result;
    elements.annotatedResultImg.classList.remove('hidden');
    elements.heatmapResultImg.classList.add('hidden');
    elements.hudStatus.textContent = 'IMAGE READY';
  };
  reader.readAsDataURL(file);
}

// Handle Video File Selection
function handleVideoSelect(file) {
  if (!file) return;
  state.selectedVideoFile = file;
  elements.analyzeVideoBtn.disabled = false;
  elements.videoDropzone.querySelector('p.text-xs').textContent = `Selected: ${file.name}`;
  elements.videoDropzone.querySelector('p.text-[10px]').textContent = `${(file.size / (1024*1024)).toFixed(1)} MB`;
}

// Run Image Analysis via REST API
async function runImageAnalysis() {
  if (!state.selectedImageFile) return;

  showLoader('Detecting people with YOLOv8...');
  elements.analyzeImageBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', state.selectedImageFile);
  formData.append('event_type', state.eventType);
  formData.append('privacy_mode', state.privacyMode);
  formData.append('conf_threshold', state.confThreshold);
  formData.append('session_id', state.sessionId);

  try {
    const res = await fetch('/api/analyze-image', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis error');

    applyAnalysisResult(data);
  } catch (err) {
    alert('Analysis failed: ' + err.message);
  } finally {
    hideLoader();
    elements.analyzeImageBtn.disabled = false;
  }
}

// Run Sample Preset Analysis
async function runSampleAnalysis(sampleId) {
  showLoader('Loading and analyzing preset crowd scenario...');
  try {
    const res = await fetch(`/api/analyze-sample/${sampleId}?privacy_mode=${state.privacyMode}`, {
      method: 'POST'
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Sample error');

    applyAnalysisResult(data);
  } catch (err) {
    alert('Preset analysis failed: ' + err.message);
  } finally {
    hideLoader();
  }
}

// Run Video Analysis via REST API
async function runVideoAnalysis() {
  if (!state.selectedVideoFile) return;

  elements.analyzeVideoBtn.disabled = true;
  elements.videoProgressWrap.classList.remove('hidden');
  showLoader('Sampling video frames & estimating crowd dynamics...');

  const formData = new FormData();
  formData.append('file', state.selectedVideoFile);
  formData.append('event_type', state.eventType);
  formData.append('privacy_mode', state.privacyMode);
  formData.append('conf_threshold', state.confThreshold);

  try {
    const res = await fetch('/api/analyze-video', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Video analysis error');

    // Update charts with video timeline
    if (data.timeline && data.timeline.length > 0) {
      updateTimelineChartFromVideo(data.timeline);
    }

    // Set peak image
    if (data.peak_annotated_image) {
      elements.viewportPlaceholder.classList.add('hidden');
      elements.annotatedResultImg.src = data.peak_annotated_image;
      elements.annotatedResultImg.classList.remove('hidden');
      elements.heatmapResultImg.classList.add('hidden');
      state.lastAnalysis = {
        annotated_image: data.peak_annotated_image,
        heatmap_image: data.peak_annotated_image
      };
      elements.downloadResultBtn.disabled = false;
    }

    // Update KPIs with peak stats
    elements.kpiCount.textContent = data.peak_count;
    elements.kpiCountSub.innerHTML = `<i data-lucide="video" class="w-3 h-3 text-indigo-400"></i><span>Avg: ${data.avg_count} | Peak: ${data.peak_count}</span>`;
    updateDensityBadges(data.peak_density, data.peak_level_key, 100);
    updateAlertStatus(data.alert);

    // Refresh history
    loadDetectionHistory();
    loadAnalyticsSummary();
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    alert('Video analysis failed: ' + err.message);
  } finally {
    hideLoader();
    elements.analyzeVideoBtn.disabled = false;
    elements.videoProgressWrap.classList.add('hidden');
  }
}

// Apply Analysis Result to Dashboard
function applyAnalysisResult(data) {
  state.lastAnalysis = data;
  elements.viewportPlaceholder.classList.add('hidden');

  // Update Viewport Images
  elements.annotatedResultImg.src = data.annotated_image;
  elements.heatmapResultImg.src = data.heatmap_image;
  elements.downloadResultBtn.disabled = false;

  if (state.currentView === 'annotated') {
    elements.annotatedResultImg.classList.remove('hidden');
    elements.heatmapResultImg.classList.add('hidden');
  } else {
    elements.annotatedResultImg.classList.add('hidden');
    elements.heatmapResultImg.classList.remove('hidden');
  }

  // Update HUD
  elements.hudStatus.textContent = 'AI DETECTED';
  elements.hudRes.textContent = `${data.width}x${data.height}`;
  elements.hudDensity.textContent = data.density_label.toUpperCase();
  elements.viewportCountBadge.textContent = `${data.count} Persons Detected`;
  elements.inferenceTimeLabel.textContent = `Inference: ${data.processing_time_ms} ms`;

  // Update KPI Count
  animateNumber(elements.kpiCount, data.count);
  elements.kpiCountSub.innerHTML = `<i data-lucide="check" class="w-3 h-3 text-emerald-400"></i><span>Detection complete</span>`;
  elements.kpiLatency.textContent = `Latency: ${data.processing_time_ms} ms`;

  // Update Density Badges & Occupancy Bar
  updateDensityBadges(data.density_label, data.level_key, data.occupancy_pct);

  // Update Event Scenario
  elements.kpiEventName.textContent = data.event_name || 'Gathering';
  if (data.details && data.details.thresholds) {
    elements.kpiThresholdText.textContent = `Cap: ${data.details.thresholds.high} Persons`;
  }

  // Update Alerts & Action SOPs
  updateAlertStatus(data.alert);

  // Play Sound Effect
  if (data.alert.sound === 'emergency') {
    soundEngine.playEmergencySiren();
  } else if (data.alert.sound === 'warning' || data.alert.sound === 'notice') {
    soundEngine.playWarningChime();
  }

  // Append point to Chart
  addChartDataPoint(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }), data.count);

  // Refresh history and analytics
  loadDetectionHistory();
  loadAnalyticsSummary();

  if (window.lucide) lucide.createIcons();
}

// Update Density Badges & Occupancy Progress
function updateDensityBadges(label, levelKey, occupancyPct) {
  elements.kpiDensityBadge.textContent = label;
  elements.kpiDensityBadge.className = `px-2.5 py-1 text-xs font-bold rounded-lg density-${levelKey}`;

  // Progress Bar
  const pct = Math.min(Math.max(occupancyPct || 10, 5), 100);
  elements.kpiOccupancyBar.style.width = `${pct}%`;

  const barColors = {
    low: 'bg-emerald-500',
    medium: 'bg-amber-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500'
  };
  elements.kpiOccupancyBar.className = `h-1.5 rounded-full transition-all duration-500 ${barColors[levelKey] || 'bg-blue-500'}`;
}

// Update Alert Banner and SOP Guidelines
function updateAlertStatus(alert) {
  elements.kpiStatusText.textContent = alert.title;
  elements.kpiStatusUrgency.textContent = alert.urgency;

  const textColors = {
    normal: 'text-emerald-400',
    advisory: 'text-amber-400',
    warning: 'text-orange-400',
    critical: 'text-red-400'
  };
  elements.kpiStatusText.className = `text-sm sm:text-base font-bold truncate ${textColors[alert.severity] || 'text-emerald-400'}`;

  // Emergency Banner
  if (alert.severity === 'critical') {
    elements.alertBanner.classList.remove('hidden');
    elements.alertBanner.className = 'border-b border-red-500/50 bg-red-950/80 text-white alert-critical-pulse';
    elements.alertBannerTitle.textContent = alert.title.toUpperCase();
    elements.alertBannerDesc.textContent = alert.summary;
  } else if (alert.severity === 'warning') {
    elements.alertBanner.classList.remove('hidden');
    elements.alertBanner.className = 'border-b border-orange-500/50 bg-orange-950/70 text-white alert-high-pulse';
    elements.alertBannerTitle.textContent = alert.title.toUpperCase();
    elements.alertBannerDesc.textContent = alert.summary;
  } else {
    elements.alertBanner.classList.add('hidden');
  }

  // SOP Guidelines Card
  elements.sopUrgencyBadge.textContent = alert.urgency;
  elements.sopUrgencyBadge.className = `px-2 py-0.5 rounded text-[10px] font-bold density-${alert.level_key}`;
  elements.sopSummary.textContent = alert.summary;

  // SOP List
  elements.sopList.innerHTML = '';
  (alert.sops || []).forEach(sop => {
    const li = document.createElement('li');
    li.className = 'flex items-start gap-2';
    const iconColor = alert.severity === 'critical' ? 'text-red-400' : (alert.severity === 'warning' ? 'text-orange-400' : 'text-emerald-400');
    li.innerHTML = `
      <i data-lucide="check-circle-2" class="w-3.5 h-3.5 ${iconColor} mt-0.5 flex-shrink-0"></i>
      <span>${sop}</span>
    `;
    elements.sopList.appendChild(li);
  });
}

// Live Webcam Feed Implementation
async function startWebcam() {
  try {
    soundEngine.init();
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });

    state.webcamStream = stream;
    elements.webcamVideo.srcObject = stream;
    elements.webcamVideo.classList.remove('hidden');
    elements.webcamOverlayCanvas.classList.remove('hidden');
    elements.viewportPlaceholder.classList.add('hidden');
    elements.annotatedResultImg.classList.add('hidden');
    elements.heatmapResultImg.classList.add('hidden');

    elements.startCamBtn.disabled = true;
    elements.stopCamBtn.disabled = false;
    elements.camStatsBar.classList.remove('hidden');
    state.isAnalyzingWebcam = true;

    // Offscreen canvas for frame capture
    const offCanvas = document.createElement('canvas');
    offCanvas.width = 640;
    offCanvas.height = 480;
    const offCtx = offCanvas.getContext('2d');

    // Run frame detection loop (~1.5s interval to ensure fast response on CPU)
    state.webcamInterval = setInterval(async () => {
      if (!state.isAnalyzingWebcam || elements.webcamVideo.readyState < 2) return;

      offCtx.drawImage(elements.webcamVideo, 0, 0, 640, 480);
      const frameBase64 = offCanvas.toDataURL('image/jpeg', 0.7);

      const startTime = performance.now();
      try {
        const res = await fetch('/api/analyze-frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: frameBase64,
            event_type: state.eventType,
            privacy_mode: state.privacyMode,
            conf_threshold: state.confThreshold,
            session_id: state.sessionId
          })
        });
        const data = await res.json();
        if (res.ok) {
          const fps = (1000 / (performance.now() - startTime)).toFixed(1);
          elements.camFpsBadge.textContent = `Processing: ${data.processing_time_ms}ms (${fps} FPS)`;
          applyLiveWebcamFrame(data);
        }
      } catch (e) {
        console.warn('Webcam frame analysis error:', e);
      }
    }, 1500);

  } catch (err) {
    alert('Webcam access error: ' + err.message + '\nPlease check camera permissions in your browser.');
  }
}

function stopWebcam() {
  state.isAnalyzingWebcam = false;
  if (state.webcamInterval) {
    clearInterval(state.webcamInterval);
    state.webcamInterval = null;
  }
  if (state.webcamStream) {
    state.webcamStream.getTracks().forEach(track => track.stop());
    state.webcamStream = null;
  }
  elements.webcamVideo.classList.add('hidden');
  elements.webcamOverlayCanvas.classList.add('hidden');
  elements.startCamBtn.disabled = false;
  elements.stopCamBtn.disabled = true;
  elements.camStatsBar.classList.add('hidden');
  elements.hudStatus.textContent = 'CAMERA STOPPED';
}

function applyLiveWebcamFrame(data) {
  // Update overlay canvas with bounding boxes
  const canvas = elements.webcamOverlayCanvas;
  canvas.width = elements.webcamVideo.videoWidth || 640;
  canvas.height = elements.webcamVideo.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const colors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#f97316',
    critical: '#ef4444'
  };
  const boxColor = colors[data.level_key] || '#10b981';

  (data.boxes || []).forEach((b, idx) => {
    ctx.strokeStyle = boxColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1);

    // Tag
    ctx.fillStyle = boxColor;
    ctx.fillRect(b.x1, Math.max(0, b.y1 - 18), 45, 18);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText(`#${idx + 1}`, b.x1 + 4, Math.max(0, b.y1 - 4));
  });

  // Update KPIs
  elements.kpiCount.textContent = data.count;
  elements.viewportCountBadge.textContent = `${data.count} Persons Detected`;
  elements.hudDensity.textContent = data.density_label.toUpperCase();
  elements.inferenceTimeLabel.textContent = `Inference: ${data.processing_time_ms} ms`;
  updateDensityBadges(data.density_label, data.level_key, data.occupancy_pct);
  updateAlertStatus(data.alert);

  if (data.alert.sound === 'emergency') {
    soundEngine.playEmergencySiren();
  }

  addChartDataPoint(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }), data.count);
}

// Chart.js Visualizations
function initCharts() {
  // 1. Time-Series Crowd Trajectory
  const trendCtx = document.getElementById('crowdTrendChart').getContext('2d');
  state.trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: ['12:00', '12:05', '12:10', '12:15', '12:20'],
      datasets: [{
        label: 'Crowd Count',
        data: [10, 18, 35, 48, 25],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#3b82f6',
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        }
      }
    }
  });

  // 2. Density Level Distribution Donut
  const donutCtx = document.getElementById('densityDonutChart').getContext('2d');
  state.donutChart = new Chart(donutCtx, {
    type: 'doughnut',
    data: {
      labels: ['Low Density', 'Medium Density', 'High Density', 'Critical Density'],
      datasets: [{
        data: [12, 8, 4, 2],
        backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
        borderWidth: 2,
        borderColor: '#0f172a'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#cbd5e1', font: { size: 10 }, boxWidth: 10 }
        }
      },
      cutout: '65%'
    }
  });
}

function addChartDataPoint(label, value) {
  if (!state.trendChart) return;
  const labels = state.trendChart.data.labels;
  const data = state.trendChart.data.datasets[0].data;

  if (labels.length > 20) {
    labels.shift();
    data.shift();
  }
  labels.push(label);
  data.push(value);
  state.trendChart.update();
}

function updateTimelineChartFromVideo(timeline) {
  if (!state.trendChart) return;
  state.trendChart.data.labels = timeline.map(t => `${t.time_sec}s`);
  state.trendChart.data.datasets[0].data = timeline.map(t => t.count);
  state.trendChart.update();
}

// Load Detection History & Table
async function loadDetectionHistory(filterType = 'all') {
  try {
    const url = filterType && filterType !== 'all' ? `/api/history?event_type=${filterType}` : '/api/history';
    const res = await fetch(url);
    const data = await res.json();
    const rows = data.history || [];

    if (rows.length === 0) {
      elements.historyTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-6 text-slate-500">
            No detections recorded yet. Perform an analysis above to populate audit logs.
          </td>
        </tr>
      `;
      return;
    }

    elements.historyTableBody.innerHTML = '';
    rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';

      const badgeClasses = {
        low: 'density-low',
        medium: 'density-medium',
        high: 'density-high',
        critical: 'density-critical'
      };

      tr.innerHTML = `
        <td class="py-2.5 px-3 font-mono text-slate-500">#${r.id}</td>
        <td class="py-2.5 px-3 font-mono text-slate-400">${r.timestamp}</td>
        <td class="py-2.5 px-3 capitalize font-medium text-slate-200">${r.source_type}</td>
        <td class="py-2.5 px-3 font-medium text-white">${r.event_name || r.event_type}</td>
        <td class="py-2.5 px-3 font-bold text-white">${r.crowd_count}</td>
        <td class="py-2.5 px-3">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClasses[r.level_key] || 'density-low'}">
            ${r.density_level}
          </span>
        </td>
        <td class="py-2.5 px-3 text-slate-300">${r.alert_title}</td>
        <td class="py-2.5 px-3 text-right font-mono text-slate-400">${r.processing_time_ms} ms</td>
      `;
      elements.historyTableBody.appendChild(tr);
    });
  } catch (e) {
    console.warn('Failed to load history:', e);
  }
}

// Load Analytics Summary
async function loadAnalyticsSummary() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    if (!res.ok) return;

    // Update Donut Chart
    if (state.donutChart && data.density_breakdown) {
      const b = data.density_breakdown;
      state.donutChart.data.datasets[0].data = [b.low || 0, b.medium || 0, b.high || 0, b.critical || 0];
      state.donutChart.update();
    }
  } catch (e) {
    console.warn('Failed to load analytics:', e);
  }
}

// Clear History
async function clearHistory() {
  if (!confirm('Are you sure you want to clear detection history?')) return;
  try {
    await fetch('/api/history', { method: 'DELETE' });
    loadDetectionHistory();
    loadAnalyticsSummary();
  } catch (e) {
    alert('Clear history error: ' + e.message);
  }
}

// Export History as CSV
async function exportHistoryCSV() {
  try {
    const res = await fetch('/api/history?limit=100');
    const data = await res.json();
    const rows = data.history || [];
    if (rows.length === 0) {
      alert('No records to export.');
      return;
    }

    const headers = ['ID', 'Timestamp', 'Source', 'Event Type', 'People Count', 'Density Level', 'Alert Status', 'Latency (ms)'];
    const csvContent = [
      headers.join(','),
      ...rows.map(r => [
        r.id,
        `"${r.timestamp}"`,
        r.source_type,
        `"${r.event_name || r.event_type}"`,
        r.crowd_count,
        `"${r.density_level}"`,
        `"${r.alert_title}"`,
        r.processing_time_ms
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crowd_monitoring_audit_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('Export CSV error: ' + e.message);
  }
}

// Download Current Frame
function downloadCurrentResult() {
  if (!state.lastAnalysis) return;
  const targetImg = state.currentView === 'annotated' ? state.lastAnalysis.annotated_image : state.lastAnalysis.heatmap_image;
  if (!targetImg) return;

  const a = document.createElement('a');
  a.href = targetImg;
  a.download = `crowd_detection_${state.currentView}_${Date.now()}.jpg`;
  a.click();
}

// Utilities
function showLoader(msg = 'Processing...') {
  elements.loaderMsg.textContent = msg;
  elements.viewportLoader.classList.remove('hidden');
}

function hideLoader() {
  elements.viewportLoader.classList.add('hidden');
}

function animateNumber(element, target) {
  const current = parseInt(element.textContent) || 0;
  const duration = 400;
  const steps = 15;
  const stepTime = duration / steps;
  const increment = (target - current) / steps;
  let count = current;
  let step = 0;

  const timer = setInterval(() => {
    step++;
    count += increment;
    element.textContent = Math.round(count);
    if (step >= steps) {
      clearInterval(timer);
      element.textContent = target;
    }
  }, stepTime);
}

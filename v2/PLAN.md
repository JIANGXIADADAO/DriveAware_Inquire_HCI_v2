# DriveAware Inquire HCI v2 — v2 Plan

**Purpose**: Driver fatigue monitoring research prototype — system perceives driver state, inquires whether to switch mode, driver decides via voice, cockpit adapts.
**Tech stack**: Python + OpenCV + MediaPipe + Whisper + pyttsx3 + Pygame + DeepSeek API (OpenAI SDK)
**Created**: 2026-05-14

## Features

| ID | Feature | Depends On | Status |
|----|---------|------------|--------|
| F001 | Camera Perception (Face Mesh + MAR) | — | planned |
| F002 | Yawn Detection (Exponential-Decay Scoring) | F001 | planned |
| F003 | FSM State Machine | F002 | planned |
| F004 | TTS Inquiry Engine | F003 | planned |
| F005 | Segmented Voice Recording Pipeline (FSM) | F003, F004 | planned |
| F006 | Continuous Voice Commands (VAD-based) | F007 | planned |
| F007 | NLP Intent Classification | — | planned |
| F008 | Cockpit Mode Switching | F003, F006 | planned |
| F009 | Cockpit HUD UI | F001, F008 | planned |
| F010 | Config Hot-Reload | — | planned |
| F011 | MAR Threshold Calibration | F001 | planned |
| F012 | CSV Data Logging | F001, F002, F003, F008 | planned |
| F013 | Thread Watchdog | F001, F004, F006 | planned |
| F014 | Help Overlay | F009 | planned |

## V2 Backlog — Architectural Improvements

Items carried forward from the original V2_PLAN.md (2026-05-14) that are not yet implemented.
Ordered by suggested implementation priority.

### B01 — Whisper Async Loading (P1-10)

**Problem:** `STTEngine.load()` calls `whisper.load_model()` synchronously in `main.py` before the Pygame loop starts, blocking 5–15s with a white screen.

**Scope:**
- `stt_engine.py`: move `load()` to a daemon thread; add `is_ready()` / `is_loading()` state queries; `transcribe()` queues until ready
- `shared_state.py`: change `whisper_ready: bool` to a three-state string `"loading"` / `"ready"` / `"failed"`
- `cockpit_ui.py`: render loading indicator text when state is `"loading"`
- `main.py`: instantiate STTEngine and enter Pygame loop immediately without waiting

**Dependencies:** None (standalone)
**Estimate:** ~1h

### B02 — STT Engine Upgrade: faster-whisper medium int8 (P1-7)

**Problem:** openai-whisper `small` has high hallucination rate on short words ("Yes"→"Yinz", "Rest"→"Res"). `nlp_parser.py` patches this with hardcoded misrecognition dictionaries.

**Scope:**
- `requirements.txt`: replace `openai-whisper` with `faster-whisper>=1.0.0`; remove `torch==2.6.0` (faster-whisper bundles ctranslate2, no PyTorch needed)
- `stt_engine.py`: replace `whisper.load_model("small")` with `faster_whisper.WhisperModel("medium", device="cuda", compute_type="int8_float16")`; adapt `transcribe()` API (segments vs result dict)
- `nlp_parser.py`: remove hardcoded Whisper-small artifacts (`yinz`, `yis`, `yass`, `yesss`, `yees`, `yas`, `yus`, `yiss`, `res`, `ress`); keep core keyword dictionary only
- `config.json`: `WHISPER_MODEL_SIZE` default `"medium"`; add `WHISPER_COMPUTE_TYPE` (`"int8_float16"` for GPU, `"int8"` for CPU)
- DeepSeek API remains unchanged (faster-whisper only replaces STT, not NLP)

**Dependencies:** B01 (async loading pairs naturally with model upgrade)
**Estimate:** ~2–3h

### B03 — Multi-Modal Perception (P1-6)

**Problem:** Fatigue detection relies solely on MAR (mouth aspect ratio). Low light and head pose changes degrade MediaPipe landmarks. No eye closure or head pose signal.

**Scope:**
- `src/perception/ear.py` (new): Eye Aspect Ratio from 6 eye-landmark indices per eye (MediaPipe 478-landmark model). Sliding window PERCLOS calculation (30s @ 15fps).
- `src/perception/head_pose.py` (new): extract pitch/yaw/roll from MediaPipe `face_blendshapes` or `face_transformation_matrix`. Focus on pitch (nodding = fatigue) and yaw (profile = occlusion).
- `src/perception/fatigue_scorer.py` (new): weighted fusion `w_mar×MAR + w_ear×EAR + w_head×head`. Initial weights `0.4 / 0.4 / 0.2` (configurable). Yawn still gives +0.5 boost as strong signal.
- `src/perception/yawn_detector.py`: refactor into `FatigueDetector` integrating all three pathways.
- `src/perception/face_mesh.py`: expose eye landmarks and face transformation matrix.
- `src/perception/camera.py`: call all three perception pipelines per frame.
- `src/core/shared_state.py`: add `debug_ear`, `debug_head_pitch`, `debug_head_yaw`.
- `src/execution/cockpit_ui.py`: render EAR and head pose in debug overlay.
- `config.json`: add EAR/head-pose threshold parameters.
- Existing tests (`test_yawn_detector.py`, `test_mar.py`) must continue to pass.

**Dependencies:** None (parallel to B01/B02, but touches perception heavily)
**Estimate:** ~4–6h

### B04 — Event Bus Architecture (P1-9)

**Problem:** All thread communication goes through SharedState flags + FSM per-frame polling. Adding a new event type requires: new SharedState field + FSM branch + thread write site. Does not scale.

**Scope:**
- `src/core/event_bus.py` (new): lightweight synchronous pub/sub — `subscribe(event_type, handler)`, `publish(event)`. Handlers run in publisher's thread (no extra threading). Exceptions are caught and logged, one handler failure does not affect others.
- Event types (dataclasses): `YawnDetectedEvent`, `TTSCompleteEvent`, `TranscriptionCompleteEvent`, `VoiceCommandEvent`, `ModeSwitchedEvent`.
- `src/core/shared_state.py`: remove control-flow fields (`yawn_detected`, `tts_done`, `worker_done`, `voice_intent`). Keep mode state, debug data, and health status.
- `src/core/state_machine.py`: refactor from `update(shared)` to `handle_event(shared, event)` — each state becomes a handler function returning new state or None.
- `src/execution/cockpit_app.py`: main loop polls event queue → calls `fsm_handle_event()` → dispatches actions.
- Update existing tests (`test_state_machine.py`) for the event-driven interface.
- Verification: adding a new event type does NOT require modifying SharedState.

**Dependencies:** Do last — touches every module, conflicts with any other in-progress work
**Estimate:** ~4–6h

---

## Academic Items (tracking only, no code changes)

| ID | Task | Status |
|----|------|--------|
| P0-1 | User study (≥20 participants, trust/annoyance/control questionnaires) | not started |
| P0-2 | A/B baseline (manual vs auto-switch vs inquiry-based) | not started |
| P0-3 | Quantitative metrics (yawn precision/recall/F1, WER, end-to-end latency) | not started |
| P0-4 | Discussion logic (inquiry cognitive cost, yawn-relaxation literature, 2-yawn threshold evidence) | not started |

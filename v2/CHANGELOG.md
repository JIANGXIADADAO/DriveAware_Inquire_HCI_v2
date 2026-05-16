# v2 Changelog

**Sealed**: 2026-05-15
**Features**: 14/14 verified

## Completed

| ID | Feature | Status |
|----|---------|--------|
| F001 | Camera Perception (Face Mesh + MAR) | verified |
| F002 | Yawn Detection (Exponential-Decay Scoring) | verified |
| F003 | FSM State Machine | verified |
| F004 | TTS Inquiry Engine | verified |
| F005 | Segmented Voice Recording Pipeline (FSM) | verified |
| F006 | Continuous Voice Commands (VAD-based) | verified |
| F007 | NLP Intent Classification | verified |
| F008 | Cockpit Mode Switching | verified |
| F009 | Cockpit HUD UI | verified |
| F010 | Config Hot-Reload | verified |
| F011 | MAR Threshold Calibration | verified |
| F012 | CSV Data Logging | verified |
| F013 | Thread Watchdog | verified |
| F014 | Help Overlay | verified |

## Code quality improvements (2026-05-15)

- Removed `_enter_rest_mode()` duplication — delegates to `_apply_mode("rest")`
- Extracted shared `resample_to_16khz()` utility (`src/utils/audio.py`)
- Simplified watchdog: moved frame counter into `_watchdog()`, fixed TTS restart `or`-chain
- Initialize `_inquiry_tts_start` in `__init__` (was implicit getattr default)
- Updated README.md / README_CN.md to reflect current 6-state FSM, segmented recording, calibration, keyboard shortcuts
- Added v2 doc links to both READMEs

## Known issues

- Whisper `small` hallucinates on short words (yinz/yass/ress patches in nlp_parser). Planned upgrade to faster-whisper medium int8 (B02).
- Camera thread constructor blocks on camera open — watchdog restart fails if camera is dead.
- VoiceListener and FSM voice_pipeline share mic device — may contend on some Windows audio drivers.
- Zero test coverage for cockpit_app.py and cockpit_ui.py (most complex modules).

## Carried over to v3

| ID | Item | Estimate |
|----|------|----------|
| B01 | Whisper Async Loading — STTEngine.load() in background thread, UI loading indicator | ~1h |
| B02 | STT Engine Upgrade — openai-whisper → faster-whisper medium int8, remove NLP misrecognition patches | ~2–3h |
| B03 | Multi-Modal Perception — add EAR + head pose + fatigue scorer fusion | ~4–6h |
| B04 | Event Bus Architecture — replace SharedState polling with pub/sub | ~4–6h |

## Academic items (tracking only)

| ID | Task | Status |
|----|------|--------|
| P0-1 | User study (≥20 participants) | not started |
| P0-2 | A/B baseline (manual vs auto-switch vs inquiry) | not started |
| P0-3 | Quantitative metrics (yawn precision/recall/F1, WER, latency) | not started |
| P0-4 | Discussion logic (inquiry cognitive cost, yawn-relaxation lit, 2-yawn threshold) | not started |

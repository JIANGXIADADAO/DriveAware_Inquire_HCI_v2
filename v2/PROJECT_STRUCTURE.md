# DriveAware Inquire HCI v2 — Project Structure (v2)

**Generated**: 2026-05-14
**Source root**: D:\MY_WORKS\WOERKSHOP\Claude_with\DriveAware_Inquire_HCI_v2

## Directory Tree

```
DriveAware_Inquire_HCI_v2/
├── main.py                          — Entry point: wires all threads, loads env, starts CockpitApp
├── config.py                        — PEP 562 __getattr__ hot-reload config bridge [F010]
├── config.json                      — Runtime configuration constants with inline comments [F010]
├── requirements.txt                 — Project dependencies (vision, audio, ML, UI)
├── requirements-lock.txt            — Locked dependency versions
├── pytest.ini                       — Pytest configuration (test paths, markers)
├── CLAUDE.md                        — Project documentation for AI coding agents
├── README.md                        — English project readme
├── README_CN.md                     — Chinese project readme
├── LICENSE                          — License file
├── .env.example                     — Environment variable template (DEEPSEEK_API_KEY)
├── .gitignore                       — Git exclusion rules
│
├── assets/
│   ├── face_landmarker.task         — MediaPipe Face Landmarker model file [F001]
│   ├── sounds/
│   │   ├── dynamic_rhythm.wav       — Dynamic mode background music [F008]
│   │   ├── rest_soothing.wav        — Rest mode background music [F008]
│   │   └── transition.wav           — Mode transition sound effect [F008]
│   └── images/
│       ├── dynamic_overlay.png      — Dynamic mode UI overlay [F008]
│       └── rest_overlay.png         — Rest mode UI overlay [F008]
│
├── src/
│   ├── __init__.py                  — Package marker
│   │
│   ├── core/
│   │   ├── __init__.py              — Package marker
│   │   ├── shared_state.py          — Thread-safe SharedState dataclass + SystemState enum [F003]
│   │   ├── modes.py                 — CockpitMode dataclass: DYNAMIC_MODE / REST_MODE presets [F008]
│   │   └── state_machine.py         — FSM update(): MONITORING→YAWN→INQUIRING→LISTENING→CONFIRMING→SWITCHING [F003]
│   │
│   ├── perception/
│   │   ├── __init__.py              — Package marker
│   │   ├── camera.py                — CameraThread: OpenCV capture → face mesh → MAR → yawn scoring [F001]
│   │   ├── face_mesh.py             — MediaPipe Face Landmarker wrapper (478-landmark model) [F001]
│   │   ├── mar.py                   — 6-point Mouth Aspect Ratio calculation (inner lip contour) [F001]
│   │   ├── yawn_detector.py         — Exponential-decay scoring: growth/decay model, cooldown, ~1.5s trigger [F002]
│   │   └── calibration.py           — 30-second 2-phase per-session MAR threshold calibration [F011]
│   │
│   ├── interaction/
│   │   ├── __init__.py              — Package marker
│   │   ├── tts_engine.py            — pyttsx3 TTS thread: queue-driven offline Chinese voice output [F004]
│   │   ├── stt_engine.py            — OpenAI Whisper STT: small model, English, with audio boost [F005, F006]
│   │   ├── nlp_parser.py            — Intent classification: keyword matching + DeepSeek API fallback [F007]
│   │   ├── audio_recorder.py        — Microphone auto-detection + segmented recording for FSM pipeline [F005]
│   │   └── voice_listener.py        — Continuous VAD-based listener: adaptive noise floor, voice commands [F006]
│   │
│   ├── execution/
│   │   ├── __init__.py              — Package marker
│   │   ├── cockpit_app.py           — Pygame main loop: FSM orchestration, watchdog, voice pipeline, mode switching [F003, F005, F008, F009, F013]
│   │   └── cockpit_ui.py            — Pygame HUD renderer: mode, climate, camera preview, MAR, mic, help [F009, F014]
│   │
│   └── utils/
│       ├── __init__.py              — Package marker
│       ├── audio.py                 — Shared audio utility: resample_to_16khz() [F005, F006]
│       └── data_logger.py           — CSV data logger: timestamp/MAR/yawn_count/mode/state [F012]
│
└── tests/
    ├── __init__.py                  — Package marker
    ├── conftest.py                  — Pytest fixtures (SharedState, YawnDetector, mock config)
    ├── test_mar.py                  — MAR calculation unit tests [F001]
    ├── test_yawn_detector.py        — YawnDetector scoring model unit tests [F002]
    ├── test_shared_state.py         — SharedState thread-safety and atomic operations tests [F003]
    ├── test_state_machine.py        — FSM state transition logic tests [F003]
    └── test_nlp_parser.py           — NLP intent classification keyword/API tests [F007]
```

## Module → Feature Mapping

| Module/File | Feature ID | Feature Name |
|-------------|-----------|--------------|
| `src/perception/camera.py` | F001 | Camera Perception (Face Mesh + MAR) |
| `src/perception/face_mesh.py` | F001 | Camera Perception (Face Mesh + MAR) |
| `src/perception/mar.py` | F001 | Camera Perception (Face Mesh + MAR) |
| `assets/face_landmarker.task` | F001 | Camera Perception (Face Mesh + MAR) |
| `tests/test_mar.py` | F001 | Camera Perception (Face Mesh + MAR) |
| `src/perception/yawn_detector.py` | F002 | Yawn Detection (Exponential-Decay Scoring) |
| `tests/test_yawn_detector.py` | F002 | Yawn Detection (Exponential-Decay Scoring) |
| `src/core/shared_state.py` | F003 | FSM State Machine |
| `src/core/state_machine.py` | F003 | FSM State Machine |
| `tests/test_shared_state.py` | F003 | FSM State Machine |
| `tests/test_state_machine.py` | F003 | FSM State Machine |
| `src/interaction/tts_engine.py` | F004 | TTS Inquiry Engine |
| `src/interaction/stt_engine.py` | F005, F006 | Voice Recording Pipeline, Continuous Voice Commands |
| `src/utils/audio.py` | F005, F006 | Voice Recording Pipeline, Continuous Voice Commands |
| `src/interaction/audio_recorder.py` | F005 | Segmented Voice Recording Pipeline (FSM) |
| `src/interaction/voice_listener.py` | F006 | Continuous Voice Commands (VAD-based) |
| `src/interaction/nlp_parser.py` | F007 | NLP Intent Classification |
| `tests/test_nlp_parser.py` | F007 | NLP Intent Classification |
| `src/core/modes.py` | F008 | Cockpit Mode Switching |
| `src/execution/cockpit_app.py` | F003, F005, F008, F009, F013 | FSM, Voice Pipeline, Mode Switch, HUD, Watchdog |
| `src/execution/cockpit_ui.py` | F009, F014 | Cockpit HUD UI, Help Overlay |
| `config.py` | F010 | Config Hot-Reload |
| `config.json` | F010 | Config Hot-Reload |
| `src/perception/calibration.py` | F011 | MAR Threshold Calibration |
| `src/utils/data_logger.py` | F012 | CSV Data Logging |

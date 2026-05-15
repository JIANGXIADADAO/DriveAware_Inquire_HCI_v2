# v2 Tasks

## F001 — Camera Perception (Face Mesh + MAR)
- [x] Implement CameraThread with OpenCV capture
- [x] Implement MediaPipe Face Landmarker wrapper
- [x] Implement 6-point MAR calculation
- [x] Wire camera frame into SharedState for UI preview
- [x] Verify: Camera preview visible in HUD, MAR value updates in real-time, face status shows "Face: OK"

## F002 — Yawn Detection (Exponential-Decay Scoring)
- [x] Implement exponential growth/decay scoring model
- [x] Implement cooldown mechanism to prevent double-counting
- [x] Wire yawn events to SharedState (increment_yawn, yawn_timestamp)
- [x] Verify: Y key simulates yawn, yawn_count increments, FSM advances to YAWN_DETECTED

## F003 — FSM State Machine
- [x] Define SystemState enum (MONITORING through SWITCHING)
- [x] Implement state transition logic with retry/abandon
- [x] Wire FSM update into main loop
- [x] Verify: State transitions print to console, Y key triggers full cycle

## F004 — TTS Inquiry Engine
- [x] Implement pyttsx3 engine in a daemon thread with queue
- [x] Wire TTS prompts from config.json for each inquiry phase
- [x] Implement tts_done/tts_speaking flags for FSM synchronization
- [x] Verify: System speaks inquiry on yawn detection, confirmation on intent match

## F005 — Segmented Voice Recording Pipeline (FSM)
- [x] Implement AudioRecorder with microphone auto-detection
- [x] Implement Whisper STT engine (small model)
- [x] Implement segmented recording loop (4s chunks, max 20s)
- [x] Wire pipeline to FSM LISTENING state via worker_done flag
- [x] Verify: After TTS inquiry, system records and transcribes, keyword triggers CONFIRMING

## F006 — Continuous Voice Commands (VAD-based)
- [x] Implement VAD with adaptive noise floor estimation
- [x] Implement speech segment detection and recording
- [x] Wire Whisper STT + NLP for continuous command recognition
- [x] Implement cooldown and TTS-speech suppression
- [x] Verify: Say "dynamic mode" / "rest mode" anytime, mode switches immediately

## F007 — NLP Intent Classification
- [x] Implement keyword matching (yes/no/rest/dynamic variants)
- [x] Implement DeepSeek API fallback for ambiguous phrases
- [x] Handle Whisper mishearings (small model artifacts)
- [x] Verify: "yes" -> dynamic, "no" -> rest, ambiguous phrases hit API fallback

## F008 — Cockpit Mode Switching
- [x] Define CockpitMode dataclass (Dynamic / Rest presets)
- [x] Implement ambient color smooth transition (COLOR_TRANSITION_SPEED)
- [x] Implement music switching via pygame.mixer
- [x] Wire keyboard shortcuts (1/2), voice commands, and FSM SWITCHING
- [x] Verify: Press 1/2 or voice command, color transitions, music changes, UI updates

## F009 — Cockpit HUD UI
- [x] Implement Pygame window with mode name and ambient color label
- [x] Implement climate display (temperature, fan speed, air direction)
- [x] Implement camera preview with MAR/threshold overlay
- [x] Implement face status and mic level indicators
- [x] Verify: All UI elements render, MAR updates, face/mic indicators respond

## F010 — Config Hot-Reload
- [x] Implement config.py with PEP 562 __getattr__ dynamic attributes
- [x] Implement config.json read/write/reload
- [x] Bind F5 key to config.reload()
- [x] Verify: Edit config.json, press F5, console confirms reload, new values take effect

## F011 — MAR Threshold Calibration
- [x] Implement Calibration class with 2-phase 30-second flow
- [x] Implement threshold formula: baseline + 0.6*(peak - baseline)
- [x] Implement config.json persistence of calibrated threshold
- [x] Render calibration progress in UI
- [x] Verify: Press C, follow prompts, new threshold displayed and saved

## F012 — CSV Data Logging
- [x] Implement DataLogger with CSV writer (timestamp, MAR, yawn_count, mode, state, event)
- [x] Implement D key toggle (start/stop)
- [x] Verify: Press D, CSV created in logs/, data rows stream in real-time

## F013 — Thread Watchdog
- [x] Implement thread health monitoring every 30 frames
- [x] Implement auto-restart with 3-attempt limit
- [x] Monitor camera, TTS, and listener threads
- [x] Verify: Crashed thread triggers restart message, recovers; 3rd failure gives up

## F014 — Help Overlay
- [x] Implement semi-transparent overlay surface
- [x] List all keyboard shortcuts with categories
- [x] Bind H key to toggle
- [x] Verify: Press H shows shortcuts, press H again hides overlay

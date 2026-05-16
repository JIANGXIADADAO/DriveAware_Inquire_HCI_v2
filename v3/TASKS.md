# v3 Tasks

## B01 — Whisper Async Loading (P1-10)
- [ ] Move STTEngine.load() to daemon thread; add is_ready() / is_loading() states
- [ ] Change SharedState.whisper_ready from bool to "loading" / "ready" / "failed"
- [ ] Render loading indicator in CockpitUI when state is "loading"
- [ ] Start Pygame loop immediately in main.py without waiting for model load
- [ ] Verify: Pygame window appears within 1s, loading text shown, STT works after load

## B02 — STT Engine Upgrade: faster-whisper medium int8 (P1-7)
- [ ] Replace openai-whisper with faster-whisper in requirements.txt; remove torch dependency
- [ ] Rewrite STTEngine: WhisperModel("medium", device="cuda", compute_type="int8_float16")
- [ ] Update transcribe() API: iterate segments, join text
- [ ] Remove hardcoded Whisper-small misrecognition words from nlp_parser.py
- [ ] Add WHISPER_COMPUTE_TYPE to config.json
- [ ] Verify: "Yes"/"No"/"Rest"/"Dynamic" single-word accuracy ≥95% (20 trials each)

## B03 — Multi-Modal Perception (P1-6)
- [ ] Create src/perception/ear.py — Eye Aspect Ratio from 6 eye landmarks per eye
- [ ] Create src/perception/head_pose.py — pitch/yaw/roll from face transformation matrix
- [ ] Create src/perception/fatigue_scorer.py — weighted fusion w_mar×MAR + w_ear×EAR + w_head×head
- [ ] Refactor YawnDetector → FatigueDetector integrating all three pathways
- [ ] Expose eye landmarks and face_transform from FaceMeshDetector
- [ ] Update CameraThread to call all three pipelines per frame
- [ ] Add debug_ear, debug_head_pitch, debug_head_yaw to SharedState
- [ ] Render EAR and head pose in CockpitUI debug overlay
- [ ] Add EAR/head-pose thresholds to config.json
- [ ] Verify: existing tests pass, normal driving → fatigue_score <0.3, nodding+yawn → ≥1.0

## B04 — Event Bus Architecture (P1-9)
- [ ] Create src/core/event_bus.py — subscribe/publish with synchronous handler dispatch
- [ ] Define event dataclasses: YawnDetected, TTSComplete, TranscriptionComplete, VoiceCommand, ModeSwitched
- [ ] Refactor SharedState: remove control-flow fields (yawn_detected, tts_done, worker_done, voice_intent)
- [ ] Refactor state_machine.py: update(shared) → handle_event(shared, event) per-state handlers
- [ ] Update CockpitApp main loop: poll event queue → fsm_handle_event() → dispatch actions
- [ ] Update CameraThread, TTSEngine, VoiceListener to publish events instead of setting flags
- [ ] Update test_state_machine.py for event-driven interface
- [ ] Verify: full yawn→TTS→record→transcribe→switch cycle works; adding new event type does not require SharedState changes

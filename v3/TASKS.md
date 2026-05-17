# v3 Tasks

## ~~B01 — Whisper Async Loading~~ (Skipped)
- **Reason**: 迁至百度云 ASR API 后零本地模型，异步加载无必要。
- **Date**: 2026-05-16

## ~~B02 — STT Engine: Baidu ASR API~~ (Done)
- [x] Replace openai-whisper + torch with requests in requirements.txt
- [x] Rewrite stt_engine.py: Baidu ASR HTTP client + OAuth token + WAV encoder
- [x] Remove Whisper-small misrecognition patches from nlp_parser.py
- [x] Add ASR_PROVIDER / dev_pid to config.json, clean Whisper residue
- [x] Add BAIDU_ASR_API_KEY / BAIDU_ASR_SECRET_KEY to .env.example
- [x] Rename SharedState.whisper_ready → stt_ready
- [x] Remove blocking stt.load() from main.py
- [x] Update README.md / README_CN.md
- [x] Clean HuggingFace cache (1.5GB), delete models/ (2.2GB), delete requirements-lock.txt
- [x] Verify: STT transcribes English speech correctly via Baidu API

## B03 — Multi-Modal Perception (P1-6) ← NEXT
- [ ] Create `src/perception/ear.py` — Eye Aspect Ratio from 6 eye landmarks per eye + PERCLOS sliding window
- [ ] Create `src/perception/head_pose.py` — pitch/yaw/roll from face blendshapes or transformation matrix
- [ ] Create `src/perception/fatigue_scorer.py` — weighted fusion: w_mar×MAR + w_ear×EAR + w_head×head
- [ ] Refactor Ya

wnDetector → FatigueDetector integrating all three perception pathways
- [ ] Expose eye landmarks and face_transform from FaceMeshDetector
- [ ] Update CameraThread to call all three pipelines per frame
- [ ] Add `debug_ear`, `debug_head_pitch`, `debug_head_yaw` to SharedState
- [ ] Render EAR and head pose values in CockpitUI debug overlay
- [ ] Add EAR/head-pose threshold parameters to config.json
- [ ] Verify: existing tests pass; normal driving → fatigue_score < 0.3; nodding+yawn → ≥ 1.0

## B04 — Event Bus Architecture (P1-9) — DO LAST
- [ ] Create `src/core/event_bus.py` — subscribe/publish with sync handler dispatch
- [ ] Define event dataclasses: YawnDetected, TTSComplete, TranscriptionComplete, VoiceCommand, ModeSwitched
- [ ] Refactor SharedState: remove control-flow fields (yawn_detected, tts_done, etc.)
- [ ] Refactor state_machine.py: update(shared) → handle_event(shared, event)
- [ ] Update CockpitApp main loop: poll event queue → fsm_handle_event() → dispatch
- [ ] Update all thread classes to publish events instead of setting flags
- [ ] Update test_state_machine.py for event-driven interface
- [ ] Verify: full yawn→TTS→record→transcribe→switch cycle; adding event type doesn't touch SharedState

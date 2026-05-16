# Proactive In-Cabin Interaction — An HCI Research Prototype

> 中文版 → [README_CN.md](README_CN.md)

> **What if the cockpit *asked* instead of *acted*?**
>
> This prototype explores a simple but underexamined idea in intelligent cockpit design: the system observes physiological cues, initiates a voice inquiry, and lets the driver decide. No automatic takeovers. No alarms. Just a question.

---

## Research Question

Current Driver Monitoring Systems (DMS) face a structural problem: **physiological signals are inherently ambiguous, yet the system must act on them.** A yawn can mean fatigue, comfort, post-meal drowsiness, or simple stretching. When a system auto-executes based on such ambiguous signals—switching drive modes, issuing alerts, adjusting the cabin—it risks misinterpreting the driver's state and, more importantly, **stripping away their decision authority.**

This raises a core HCI question:

> *Can we shift the cockpit from command-based automation to inquiry-based collaboration, where the system perceives and suggests, but the human always decides?*

---

## Interaction Philosophy

### Inquiry over Automation

The system does not auto-execute. When it detects a meaningful cue (e.g., accumulated yawns suggesting low-arousal relaxation), it asks:

> *"You seem relaxed. Would you like to change to Dynamic Mode?"*

The driver says yes or no. That's it. The system handles **perception + suggestion**; the human retains **decision + confirmation.** This is **Shared Control** extended from the steering wheel to the entire cockpit environment.

### Yawn as Cue, Not Alarm

Conventional DMS treats driver state cues—especially yawns—as deterministic danger signals requiring immediate intervention. We argue this is a category error. Yawns are **contextual, multi-causal physiological events**, not fatigue alarms. Treating them as cues rather than triggers means the system *asks* rather than *acts*, resolving ambiguity through dialogue instead of guessing.

### Preserving Human Decision Authority

Every state transition is gated by explicit user behavior:
- The system *observes* but does not *judge*
- The system *suggests* but does not *force*
- The user feels *noticed*, not *monitored*; *in control*, not *overridden*

Each full interaction cycle—observe → inquire → confirm → execute—functions as a **micro-trust event**: the system proves itself predictable, cancellable, and bounded.

### Quiet by Default

Rest Mode is the default state. The system stays silent unless it accumulates sufficient evidence (≥2 yawn events within the Rest Mode context). This embodies a design stance: **silence over interruption, maintaining the current state over imposing change.**

---

## How It Works (Conceptual)

```
 Driver state cue           System inquiry            Driver response         Outcome
 (yawn detected)    →    "Would you like to        →    "Yes" / "No"     →    Switch / Stay
                          switch modes?"
```

### Two Interaction Paths

| Path | Trigger | Direction | Example |
|---|---|---|---|
| **Path A** | Yawn cue accumulation (≥2 in Rest Mode) | System initiates | System notices relaxation → asks about switching |
| **Path B** | Continuous voice command | Driver initiates | Driver says *"switch to dynamic mode"* anytime |

Path B always overrides Path A. The driver's explicit command takes priority over any system-initiated inquiry. Path A retries once on unrecognized or silent responses (with distinct prompts for silence vs. unintelligible speech), then silently returns to monitoring—avoiding the common assistant failure mode of repeated, escalating prompts.

### A Shared Control Loop

The system runs a 6-state non-blocking loop: **Monitoring → Yawn Detected → Inquiring → Listening → Confirming → Switching** → back to Monitoring. States are gated exclusively by user-relevant events (yawn detected, speech transcribed, intent parsed), not by system-internal timers.

---

## System Overview

```
┌─────────────────────────────────────────────┐
│                  Execution                   │
│     ambient light · sound · climate · UI     │
├─────────────────────────────────────────────┤
│                 Interaction                  │
│          TTS inquiry · STT · NLP             │
├─────────────────────────────────────────────┤
│                    Core                      │
│          Shared State · FSM · Modes          │
├─────────────────────────────────────────────┤
│                 Perception                   │
│     Camera · Face Landmarks · MAR Scoring    │
└─────────────────────────────────────────────┘
```

### Mode Concept

| | Rest Mode *(default)* | Dynamic Mode |
|---|---|---|
| Ambient light | Cool blue | Warm orange |
| Sound | Soothing | High-tempo |
| Virtual climate | 26°C / mild | 18°C / strong |
| Meaning | Driver prefers current comfort | Driver wants a more alerting environment |

The two modes are not simply "sport vs. comfort"—they represent two **user intent paths**: accepting the system's proactive suggestion (Dynamic) or declining to maintain the status quo (Rest).

---

## Interaction Flow

```
Monitoring ──yawn detected (×2)──→ Yawn Detected → Inquiring ──TTS done──→ Listening
                                                                                 │
                                                                         ┌───────┴────────┐
                                                                         ▼                ▼
                                                                    "dynamic"          "rest"
                                                                         │                │
                                                                         ▼                ▼
                                                                    Confirming        Confirming
                                                                         │                │
                                                                         ▼                ▼
                                                                    Switch to         Stay in
                                                                  Dynamic Mode      Rest Mode
```

Silence or unrecognised speech retries once (distinct prompts for each case). After the second failure, the system gives up and returns to Monitoring.

---

## Implementation

**Perception**: Camera → MediaPipe Face Landmarks (478-point model) → Mouth Aspect Ratio (MAR) → Exponential-decay yawn scoring. Not simple frame-counting: brief landmark jitter does not reset accumulated evidence. Yawn requires ~1.5s sustained wide mouth. Per-session MAR threshold calibration available (press `C`).

**Voice Pipeline**: pyttsx3 TTS inquiry → Segmented recording (4-second chunks, up to 20 seconds, stops on first keyword hit) → Baidu Cloud ASR API (HTTP POST, zero local model, 50k free calls/day) → Two-tier NLP (keyword matching at 0ms latency; DeepSeek API as fallback). Separate continuous VAD-based listener for unsolicited voice commands—always on, always bypasses the FSM.

**State Management**: Thread-safe `SharedState` with a 6-state FSM polled at 60fps by the Pygame main loop. Independent threads for camera capture, TTS, and continuous voice listening. Thread watchdog auto-restarts crashed threads up to 3 times.

**Config**: All parameters in `config.json` (~90 keys across perception, audio, VAD, TTS, UI, ASR). Hot-reload at runtime with `F5`—no restart needed. Per-session MAR calibration writes threshold back to config.

**Cross-platform**: Tested on Windows (pyttsx3 via SAPI5, Baidu ASR API). STT is cloud-based and platform-independent. macOS (NSSpeechSynthesizer) and Linux (espeak) TTS backends are available but untested.

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env       # add BAIDU_ASR_API_KEY + BAIDU_ASR_SECRET_KEY (required for STT), DEEPSEEK_API_KEY (optional — keyword matching works without it)
python main.py
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Switch to Dynamic Mode |
| `2` | Switch to Rest Mode |
| `C` | Calibrate personal MAR threshold (30s) |
| `D` | Toggle CSV data logging |
| `F5` | Hot-reload `config.json` |
| `H` | Toggle help overlay |
| `Y` / `Z` | Simulate yawn (debug) |
| `Esc` | Quit |

---

## Current Limitations (Research Scope)

This is a **desktop research prototype**, not a production system. Known gaps:

- **No user study yet** — design claims about trust, agency, and non-intrusiveness are not yet empirically validated
- **Single-modality perception** — MAR only; eye aspect ratio, head pose, and other fatigue signals not yet fused
- **Cloud-dependent STT** — Baidu ASR API requires internet; free tier caps at 50k calls/day. Local STT (faster-whisper) was attempted but blocked by ctranslate2 segfault on this machine
- **Desktop simulation** — no real driving task, no steering wheel, no in-vehicle noise environment
- **MAR threshold calibration is per-session only** — does not persist across restarts (factory default restored on each launch)

---

## Repository Structure

```
├── src/
│   ├── core/                # SharedState, FSM, CockpitMode
│   ├── perception/          # Camera, Face Mesh, MAR, YawnDetector, Calibration
│   ├── interaction/         # TTS, STT, NLP, VoiceListener, AudioRecorder
│   ├── execution/           # CockpitApp (main loop), CockpitUI (HUD renderer)
│   └── utils/               # CSV Data Logger, audio utilities
├── tests/                   # pytest suite (41 tests)
├── assets/                  # MediaPipe model, sounds, images
├── v2/                      # Planning docs — current version (PLAN, FLOW, TASKS, STRUCTURE, CHANGELOG)
├── v3/                      # Planning docs — next version (in progress)
├── main.py                  # Entry point
├── config.py                # Config bridge (PEP 562 __getattr__)
├── config.json              # All runtime parameters (hot-reloadable)
└── CLAUDE.md                # Project documentation for AI coding agents
```

### Project Documentation

| Document | Description |
|----------|-------------|
| [v2/PLAN.md](v2/PLAN.md) | Feature list (F001–F014), architectural backlog (B01–B04), academic tracking items |
| [v2/FLOW.md](v2/FLOW.md) | Feature dependency graph (Mermaid) with per-feature verification criteria |
| [v2/TASKS.md](v2/TASKS.md) | Per-feature task checklist — all 14 features verified complete |
| [v2/CHANGELOG.md](v2/CHANGELOG.md) | v2 completion record, known issues, items carried over to v3 |
| [v2/PROJECT_STRUCTURE.md](v2/PROJECT_STRUCTURE.md) | Full directory tree with module descriptions and feature-ID annotations |
| [v3/PLAN.md](v3/PLAN.md) | v3 plan — B02 STT migration to Baidu ASR API, pending architectural items |

## License

[MIT](LICENSE)

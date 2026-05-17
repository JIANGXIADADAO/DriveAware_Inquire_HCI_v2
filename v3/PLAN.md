# DriveAware Inquire HCI v2 — v3 Plan

**Created**: 2026-05-15
**Carried over from**: v2

## Baseline Features (from v2, all verified)

| ID | Feature | Depends On | Status |
|----|---------|------------|--------|
| F001 | Camera Perception (Face Mesh + MAR) | — | verified |
| F002 | Yawn Detection (Exponential-Decay Scoring) | F001 | verified |
| F003 | FSM State Machine | F002 | verified |
| F004 | TTS Inquiry Engine | F003 | verified |
| F005 | Segmented Voice Recording Pipeline (FSM) | F003, F004 | verified |
| F006 | Continuous Voice Commands (VAD-based) | F007 | verified |
| F007 | NLP Intent Classification | — | verified |
| F008 | Cockpit Mode Switching | F003, F006 | verified |
| F009 | Cockpit HUD UI | F001, F008 | verified |
| F010 | Config Hot-Reload | — | verified |
| F011 | MAR Threshold Calibration | F001 | verified |
| F012 | CSV Data Logging | F001, F002, F003, F008 | verified |
| F013 | Thread Watchdog | F001, F004, F006 | verified |
| F014 | Help Overlay | F009 | verified |

## Architectural Backlog (carried over from v2)

| ID | Item | Estimate | Status |
|----|------|----------|--------|
| B01 | Whisper Async Loading | ~1h | **Skipped** — faster-whisper 加载快，异步无必要 |
| B02 | STT Engine Upgrade: faster-whisper medium int8 | ~2–3h | **Failed** — ctranslate2 segfault，CPU/CUDA 均崩溃 |
| B03 | Multi-Modal Perception (EAR + head pose + fatigue scorer) | ~4–6h | Pending |
| B04 | Event Bus Architecture | ~4–6h | Pending (do last) |

### B02 failure → Baidu ASR API migration (2026-05-16)

**Root cause:** ctranslate2 在此机器上 Segfault（tiny/medium、CPU/CUDA、int8/float32 全崩），faster-whisper 不可用。尝试 FunASR/SenseVoice 替代，但其依赖 PyTorch（~2GB）失去轻量性。

**Resolution:** 放弃本地方案，迁至百度智能云短语音识别 API：
- 免费 5 万次/天，Token 鉴权，纯 `requests` POST，零本地模型
- `stt_engine.py` 重写为百度 API 调用（含 Token 自动刷新、WAV 封装）
- `requirements.txt`: `faster-whisper>=1.0.0` → `requests>=2.28.0`
- `config.json`: 清理所有 Whisper/faster-whisper/SenseVoice 残留，新增 `ASR_PROVIDER: "baidu"`
- `.env` 新增 `BAIDU_ASR_API_KEY` / `BAIDU_ASR_SECRET_KEY`
- `nlp_parser.py`: B02 时已删除 Whisper-small 修补词条，保持
- 清理 `D:\.cache\huggingface\` 下 1.5GB 损坏模型缓存

**Fix: 语言参数** — Baidu ASR 默认 `dev_pid=1537`（普通话），payload 未指定时英文被听成中文。添加 `"dev_pid": 1737`（英文模型）解决。

## Academic Items (tracking only, no code changes)

| ID | Task | Status |
|----|------|--------|
| P0-1 | User study (≥20 participants) | not started |
| P0-2 | A/B baseline (manual vs auto-switch vs inquiry) | not started |
| P0-3 | Quantitative metrics (yawn precision/recall/F1, WER, latency) | not started |
| P0-4 | Discussion logic (inquiry cognitive cost, yawn-relaxation lit, 2-yawn threshold) | not started |

# v3 Changelog

**Version**: v3
**Base**: v2 (2026-05-15, 14/14 features verified)

## B01 — Whisper Async Loading: Skipped

**Decision (2026-05-16)**: B02 迁至百度云 ASR API 后，零本地模型加载，异步加载无必要。B01 随 B02 方案变更自然废弃。

## B02 — STT Engine: faster-whisper → Baidu ASR API (completed 2026-05-16)

**Root cause**: ctranslate2 segfault 在所有配置下（tiny/medium、CPU/CUDA、int8/float32）。FunASR/SenseVoice 替代方案依赖 PyTorch ~2GB，失去轻量性。最终放弃本地方案。

**Migration**: openai-whisper `small` → 百度智能云短语音识别 API
- 免费 5 万次/天，Token 鉴权 (OAuth)，纯 `requests` POST，零本地模型
- `dev_pid=1737` (英语模型)，解决英文→中文误识别问题

**Files changed**:
- `src/interaction/stt_engine.py` — 完全重写：Baidu ASR HTTP 客户端 + OAuth Token 自动刷新 + WAV 封装 + 音频增益 boost
- `src/interaction/nlp_parser.py` — 删除 Whisper-small 误识别修补词条 (yinz/yis/yass/ress 等)
- `requirements.txt` — `openai-whisper` + `torch==2.6.0` → `requests>=2.28.0`
- `config.json` — 新增 `ASR_PROVIDER: "baidu"`，清理 Whisper 残留 (`WHISPER_MODEL_SIZE` 等)
- `.env.example` — 新增 `BAIDU_ASR_API_KEY`、`BAIDU_ASR_SECRET_KEY`
- `src/core/shared_state.py` — `whisper_ready: bool` → `stt_ready: bool`
- `src/execution/cockpit_app.py` — 适配 stt_ready 重命名
- `src/interaction/voice_listener.py` — 适配 stt_ready 重命名
- `main.py` — 移除同步 `stt.load()` 阻塞调用
- `README.md` / `README_CN.md` — 更新 STT 描述为 Baidu ASR
- 清理 `D:\.cache\huggingface\` 下 1.5GB 损坏模型缓存

**Cleanup**:
- 删除 `requirements-lock.txt` (stale)
- 删除 `models/` 目录 (2.2GB failed faster-whisper experiment)
- 新增 `src/utils/audio.py` — 共享 `resample_to_16khz()` 工具

## Architecture Backlog Status

| ID | Item | Status |
|----|------|--------|
| B01 | Whisper Async Loading | Skipped (cloud API eliminates need) |
| B02 | STT Engine: Baidu ASR API | **Done** |
| B03 | Multi-Modal Perception | Pending ← **next** |
| B04 | Event Bus Architecture | Pending (do last) |

## Academic Items (tracking only)

| ID | Task | Status |
|----|------|--------|
| P0-1 | User study (≥20 participants) | not started |
| P0-2 | A/B baseline (manual vs auto-switch vs inquiry) | not started |
| P0-3 | Quantitative metrics (yawn precision/recall/F1, WER, latency) | not started |
| P0-4 | Discussion logic (inquiry cognitive cost, yawn-relaxation lit, 2-yawn threshold) | not started |

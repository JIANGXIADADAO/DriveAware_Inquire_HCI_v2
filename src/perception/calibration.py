"""Personalized MAR threshold calibration.

30-second flow:
  Phase 1 (10s): neutral face → MAR_baseline
  Phase 2 (10s): one yawn    → MAR_yawn_peak

Threshold = baseline + 0.6 × (peak - baseline)
"""

import time


class Calibration:
    PHASE_NEUTRAL = "neutral"
    PHASE_YAWN = "yawn"
    PHASE_DONE = "done"
    PHASE_IDLE = "idle"

    def __init__(self):
        self.state = self.PHASE_IDLE
        self._mar_samples: dict[str, list[float]] = {
            self.PHASE_NEUTRAL: [],
            self.PHASE_YAWN: [],
        }
        self._start_time = 0.0
        self._phase_duration = 10.0
        self.mar_baseline = 0.0
        self.mar_yawn_peak = 0.0
        self.computed_threshold = 0.0
        self.countdown = 0.0
        self.saved = False  # whether result has been persisted to config.json

    def start(self) -> None:
        self._start_time = time.time()
        self.state = self.PHASE_NEUTRAL
        self._mar_samples = {self.PHASE_NEUTRAL: [], self.PHASE_YAWN: []}
        self.mar_baseline = 0.0
        self.mar_yawn_peak = 0.0
        self.computed_threshold = 0.0
        self.saved = False
        print("[Calibration] Phase 1 — keep a neutral face for 10 seconds")

    def update(self, mar: float) -> None:
        if self.state in (self.PHASE_IDLE, self.PHASE_DONE):
            return

        elapsed = time.time() - self._start_time
        self.countdown = max(0.0, self._phase_duration - elapsed)

        if elapsed > self._phase_duration:
            self._advance()
            return

        if mar > 0.0 and self.state in self._mar_samples:
            self._mar_samples[self.state].append(mar)

    def _advance(self) -> None:
        if self.state == self.PHASE_NEUTRAL:
            self.state = self.PHASE_YAWN
            self._start_time = time.time()
            print("[Calibration] Phase 2 — do one yawn now")
        elif self.state == self.PHASE_YAWN:
            self.state = self.PHASE_DONE
            self._compute()
            print(
                f"[Calibration] Done — baseline={self.mar_baseline:.3f}, "
                f"peak={self.mar_yawn_peak:.3f}, "
                f"threshold={self.computed_threshold:.3f}"
            )

    def _compute(self) -> None:
        neutrals = self._mar_samples[self.PHASE_NEUTRAL]
        yawns = self._mar_samples[self.PHASE_YAWN]
        self.mar_baseline = sum(neutrals) / len(neutrals) if neutrals else 0.25
        self.mar_yawn_peak = max(yawns) if yawns else 0.6
        # 60% from baseline to peak
        self.computed_threshold = self.mar_baseline + 0.6 * (self.mar_yawn_peak - self.mar_baseline)

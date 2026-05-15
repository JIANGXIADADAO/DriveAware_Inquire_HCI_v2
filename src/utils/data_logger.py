"""CSV data logger for offline analysis of perception parameters.

Toggle with D key in the cockpit app.  Writes to logs/ directory.
"""

import csv
import time
from pathlib import Path


class DataLogger:
    def __init__(self, output_dir: str = "logs"):
        self.output_dir = Path(output_dir)
        self._file = None
        self._writer = None
        self.enabled = False

    def toggle(self) -> None:
        if self.enabled:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"session_{ts}.csv"
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow([
            "timestamp", "mar", "yawn_count", "active_mode",
            "system_state", "event",
        ])
        self.enabled = True
        print(f"[DataLogger] Started → {path}")

    def stop(self) -> None:
        self.enabled = False
        if self._file:
            self._file.close()
            self._file = None
            self._writer = None
            print("[DataLogger] Stopped")

    def log(self, mar: float, yawn_count: int, active_mode: str,
            system_state: str, event: str = "") -> None:
        if not self.enabled or not self._writer:
            return
        self._writer.writerow([
            f"{time.time():.3f}", f"{mar:.4f}", yawn_count,
            active_mode, system_state, event,
        ])

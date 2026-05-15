"""
DriveAware configuration — JSON-backed with F5 hot-reload.

All constants are stored in config.json.  Edit the JSON and press F5 at runtime
to reload without restarting.  Consumer code uses ``config.NAME`` unchanged.
"""

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).parent / "config.json"
CONFIG_PATH = _CONFIG_PATH  # Public API — avoid referencing _CONFIG_PATH externally
_data: dict[str, Any] = {}


def _load() -> dict[str, Any]:
    """Read config.json, skip keys starting with '_' (comment fields)."""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def reload() -> None:
    """Re-read config.json.  Bound to F5 in the cockpit app."""
    global _data
    try:
        _data = _load()
        print("[config] Reloaded config.json")
    except Exception as e:
        print(f"[config] Reload failed, keeping current values: {e}")


def save(updates: dict[str, Any]) -> None:
    """Merge updates into config.json and persist to disk."""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    raw.update(updates)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4, ensure_ascii=False)
    reload()


# --- PEP 562 module-level __getattr__ ----------------------------------
# Every ``config.X`` access that isn't resolved as a normal module attribute
# falls through to this function, which reads from the live _data dict.
# Hot-reload works transparently — no consumer code changes needed.


def __getattr__(name: str) -> Any:
    try:
        return _data[name]
    except KeyError:
        raise AttributeError(f"module 'config' has no attribute '{name}'") from None


def __dir__() -> list[str]:
    """Support IDE autocomplete and dir()."""
    return sorted(_data.keys())


# Load on first import
_data = _load()

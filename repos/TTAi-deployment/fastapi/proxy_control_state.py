from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_FILE_PATH = Path(__file__).resolve()
if len(_FILE_PATH.parents) >= 4:
    WORKSPACE_ROOT = _FILE_PATH.parents[3]
else:
    # Docker/container fallback where the app is mounted directly at /app
    WORKSPACE_ROOT = _FILE_PATH.parent
STATE_DIR = WORKSPACE_ROOT / "state"
STATE_PATH = STATE_DIR / "proxy_control_state.json"

DEFAULT_STATE: Dict[str, Any] = {
    "version": 1,
    "updated_at": None,
    "mode": "stabilize",
    "hedge": {
        "enabled": False,
        "delay_seconds": 0.35,
    },
    "backends": {
        "local-fastapi-8000": {"enabled": True, "weight": 20},
        "remote-workop-8000": {"enabled": True, "weight": 80},
        "local-hybrid-8005": {"enabled": False, "weight": 0},
    },
}

ALLOWED_MODES = {"stabilize", "remote-first", "balanced-lite", "diagnostic"}
ALLOWED_BACKEND_IDS = {"local-fastapi-8000", "remote-workop-8000", "local-hybrid-8005"}


def _deep_copy(value: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(value))


def _ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_proxy_control_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return _deep_copy(DEFAULT_STATE)
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return _deep_copy(DEFAULT_STATE)

    merged = _deep_copy(DEFAULT_STATE)
    merged.update({k: v for k, v in data.items() if k not in {"hedge", "backends"}})
    if isinstance(data.get("hedge"), dict):
        merged["hedge"].update(data["hedge"])
    if isinstance(data.get("backends"), dict):
        for backend_id, backend_state in data["backends"].items():
            if backend_id in merged["backends"] and isinstance(backend_state, dict):
                merged["backends"][backend_id].update(backend_state)
    return merged


def save_proxy_control_state(state: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_state_dir()
    state = _deep_copy(state)
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def set_proxy_mode(mode: str) -> Dict[str, Any]:
    mode = (mode or "").strip().lower()
    if mode not in ALLOWED_MODES:
        raise ValueError(f"Unsupported proxy mode: {mode}")
    state = load_proxy_control_state()
    state["mode"] = mode
    return save_proxy_control_state(state)


def set_proxy_hedge(enabled: bool, delay_seconds: float) -> Dict[str, Any]:
    if delay_seconds < 0 or delay_seconds > 5:
        raise ValueError("delay_seconds must be between 0 and 5")
    state = load_proxy_control_state()
    state["hedge"] = {
        "enabled": bool(enabled),
        "delay_seconds": float(delay_seconds),
    }
    return save_proxy_control_state(state)


def set_backend_enabled(backend_id: str, enabled: bool) -> Dict[str, Any]:
    if backend_id not in ALLOWED_BACKEND_IDS:
        raise ValueError(f"Unsupported backend id: {backend_id}")
    state = load_proxy_control_state()
    state["backends"].setdefault(backend_id, {})
    state["backends"][backend_id]["enabled"] = bool(enabled)
    return save_proxy_control_state(state)


def set_backend_weight(backend_id: str, weight: int) -> Dict[str, Any]:
    if backend_id not in ALLOWED_BACKEND_IDS:
        raise ValueError(f"Unsupported backend id: {backend_id}")
    if weight < 0 or weight > 100:
        raise ValueError("weight must be between 0 and 100")
    state = load_proxy_control_state()
    state["backends"].setdefault(backend_id, {})
    state["backends"][backend_id]["weight"] = int(weight)
    return save_proxy_control_state(state)

import time
import config
from src.core.shared_state import SystemState


def update(shared):
    state = shared.system_state

    if state == SystemState.MONITORING:
        yawn, count = shared.get("yawn_detected", "yawn_count")
        # Only trigger proactive interaction when in Rest Mode
        if yawn and count >= 2 and shared.active_mode == "rest":
            shared.update(
                system_state=SystemState.YAWN_DETECTED,
                yawn_detected=False,
                yawn_count=0,
            )
            return

    elif state == SystemState.YAWN_DETECTED:
        # Brief gate to debounce, then proceed.
        # Clear tts_done — a stale True from a prior voice-command TTS
        # would otherwise cause INQUIRING to jump straight to LISTENING.
        shared.update(system_state=SystemState.INQUIRING, tts_done=False)
        return

    elif state == SystemState.INQUIRING:
        # Transition handled by _handle_fsm_actions in cockpit_app.py.
        # The FSM must not advance on tts_done here — a stale True from a
        # prior voice-command confirmation TTS would skip the inquiry TTS.
        pass

    elif state == SystemState.LISTENING:
        # Segmented recording pipeline sets final intent + worker_done in one go.
        if shared.worker_done:
            intent, retries = shared.get("last_intent", "retry_count")
            shared.update(worker_done=False)
            if intent in ("dynamic", "rest"):
                shared.update(
                    system_state=SystemState.CONFIRMING,
                    retry_count=0,
                )
            elif retries < config.MAX_RETRIES:
                shared.update(
                    system_state=SystemState.INQUIRING,
                    retry_count=retries + 1,
                )
            else:
                # Exhausted — route through INQUIRING so the exhaustion
                # prompt (PROMPT_RETRY_EXHAUSTED) is spoken before giving up.
                shared.update(
                    system_state=SystemState.INQUIRING,
                    retry_count=retries + 1,
                )
            return

    elif state == SystemState.CONFIRMING:
        if shared.tts_done:
            shared.update(
                system_state=SystemState.SWITCHING,
                tts_done=False,
            )
            return

    elif state == SystemState.SWITCHING:
        shared.update(
            system_state=SystemState.MONITORING,
            yawn_count=0, yawn_detected=False,
        )
        return

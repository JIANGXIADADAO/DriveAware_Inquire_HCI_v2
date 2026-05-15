from src.core.shared_state import SystemState
from src.core.state_machine import update as fsm_update


def test_monitoring_stays_when_no_yawn(shared):
    shared.update(active_mode="rest", yawn_detected=False, yawn_count=0)
    fsm_update(shared)
    assert shared.system_state == SystemState.MONITORING


def test_monitoring_stays_in_dynamic_mode(shared):
    shared.update(active_mode="dynamic", yawn_detected=True, yawn_count=5)
    fsm_update(shared)
    assert shared.system_state == SystemState.MONITORING


def test_monitoring_to_yawn_detected(shared):
    shared.update(active_mode="rest", yawn_detected=True, yawn_count=2)
    fsm_update(shared)
    assert shared.system_state == SystemState.YAWN_DETECTED
    assert shared.yawn_detected is False
    assert shared.yawn_count == 0


def test_yawn_detected_to_inquiring(shared):
    shared.update(system_state=SystemState.YAWN_DETECTED)
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING


def test_inquiring_stays_on_tts_done_in_fsm(shared):
    """FSM no longer advances INQUIRING→LISTENING on tts_done.

    The transition is driven by _handle_fsm_actions in cockpit_app.py
    so that a stale tts_done from a voice-command confirmation TTS
    cannot skip the inquiry TTS."""
    shared.update(system_state=SystemState.INQUIRING, tts_done=True)
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING, (
        "FSM must stay in INQUIRING — transition handled by _handle_fsm_actions"
    )


def test_listening_to_confirming_dynamic(shared):
    """LISTENING → CONFIRMING when intent is 'dynamic'."""
    shared.update(
        system_state=SystemState.LISTENING,
        worker_done=True,
        last_intent="dynamic",
    )
    fsm_update(shared)
    assert shared.system_state == SystemState.CONFIRMING


def test_listening_to_confirming_rest(shared):
    """LISTENING → CONFIRMING when intent is 'rest'."""
    shared.update(
        system_state=SystemState.LISTENING,
        worker_done=True,
        last_intent="rest",
    )
    fsm_update(shared)
    assert shared.system_state == SystemState.CONFIRMING


def test_listening_retry_on_silence(shared):
    """LISTENING → INQUIRING when user didn't speak (silence)."""
    shared.update(
        system_state=SystemState.LISTENING,
        worker_done=True,
        last_intent="silence",
        retry_count=0,
    )
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING
    assert shared.retry_count == 1


def test_listening_retry_on_unknown(shared):
    """LISTENING → INQUIRING when intent is 'unknown'."""
    shared.update(
        system_state=SystemState.LISTENING,
        worker_done=True,
        last_intent="unknown",
        retry_count=0,
    )
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING
    assert shared.retry_count == 1


def test_listening_retry_exhausted(shared):
    """LISTENING → INQUIRING when retries exhausted (so exhaustion prompt plays).

    The MONITORING transition now happens in _handle_fsm_actions after the
    exhaustion TTS finishes, not directly in the FSM.
    """
    shared.update(
        system_state=SystemState.LISTENING,
        worker_done=True,
        last_intent="unknown",
        retry_count=1,
    )
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING, (
        "FSM must route exhaustion through INQUIRING so "
        "PROMPT_RETRY_EXHAUSTED is spoken before giving up"
    )
    assert shared.retry_count == 2, (
        "retry_count increments so INQUIRING handler's else branch fires"
    )


def test_confirming_to_switching(shared):
    shared.update(system_state=SystemState.CONFIRMING, tts_done=True)
    fsm_update(shared)
    assert shared.system_state == SystemState.SWITCHING


def test_inquiring_clears_stale_tts_done_from_voice_cmd(shared):
    """YAWN_DETECTED → INQUIRING must clear tts_done, even if stale from
    a prior voice-command confirmation TTS.

    Repro: voice cmd → rest → TTS confirmation finishes (tts_done=True)
    → back in MONITORING. Then 2 yawns trigger the inquiry flow.
    Without clearing tts_done at the YAWN_DETECTED→INQUIRING transition,
    the FSM sees the stale flag and jumps straight to LISTENING — skipping
    the inquiry TTS entirely.
    """
    # Simulate: voice command TTS finished, system back in MONITORING
    shared.update(
        system_state=SystemState.MONITORING,
        active_mode="rest",
        tts_done=True,          # stale from voice-cmd TTS
        yawn_detected=False,
        yawn_count=0,
    )
    # Frame 1: 2 yawns detected → YAWN_DETECTED
    shared.update(yawn_detected=True, yawn_count=2)
    fsm_update(shared)
    assert shared.system_state == SystemState.YAWN_DETECTED

    # Frame 2: YAWN_DETECTED → INQUIRING (must clear stale tts_done)
    fsm_update(shared)
    assert shared.system_state == SystemState.INQUIRING
    assert shared.tts_done is False, (
        "BUG: tts_done still True after entering INQUIRING. "
        "Stale flag from voice-command TTS causes FSM to jump to LISTENING "
        "without playing the inquiry TTS."
    )


def test_switching_to_monitoring(shared):
    shared.update(system_state=SystemState.SWITCHING)
    fsm_update(shared)
    assert shared.system_state == SystemState.MONITORING
    assert shared.yawn_count == 0


def test_full_cycle_smoke(shared):
    """End-to-end smoke test: MONITORING → ... → MONITORING (dynamic intent)."""
    shared.update(active_mode="rest")
    shared.increment_yawn()
    shared.increment_yawn()

    fsm_update(shared)  # MONITORING → YAWN_DETECTED
    assert shared.system_state == SystemState.YAWN_DETECTED
    fsm_update(shared)  # YAWN_DETECTED → INQUIRING
    assert shared.system_state == SystemState.INQUIRING
    shared.update(tts_done=True)
    # INQUIRING→LISTENING is now driven by _handle_fsm_actions,
    # not the FSM.  Jump to LISTENING manually for this smoke test.
    shared.update(system_state=SystemState.LISTENING, tts_done=False)
    assert shared.system_state == SystemState.LISTENING
    shared.update(last_intent="dynamic", worker_done=True)
    fsm_update(shared)  # LISTENING → CONFIRMING
    assert shared.system_state == SystemState.CONFIRMING
    shared.update(tts_done=True)
    fsm_update(shared)  # CONFIRMING → SWITCHING
    assert shared.system_state == SystemState.SWITCHING
    fsm_update(shared)  # SWITCHING → MONITORING
    assert shared.system_state == SystemState.MONITORING

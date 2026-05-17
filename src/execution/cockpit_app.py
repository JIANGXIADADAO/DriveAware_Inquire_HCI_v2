import os
import sys
import threading
import time
import pygame
import config
from src.core.modes import DYNAMIC_MODE, REST_MODE
from src.core.shared_state import SystemState
from src.core.state_machine import update as fsm_update
from src.execution.cockpit_ui import CockpitUI
from src.perception.calibration import Calibration
from src.utils.data_logger import DataLogger

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets"
)


class CockpitApp:
    def __init__(self, shared_state, tts_engine, stt_engine, nlp_parser,
                 audio_recorder, camera_thread=None, voice_listener=None):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        )
        pygame.display.set_caption("Intelligent Cockpit - Multimodal HCI System")
        self.clock = pygame.time.Clock()
        self.shared = shared_state
        self.tts = tts_engine
        self.stt = stt_engine
        self.nlp = nlp_parser
        self.recorder = audio_recorder

        self.current_mode = REST_MODE
        self.shared.update(active_mode="rest")
        self._light_color = list(config.BG_COLOR)
        self._current_track = None
        self.ui = CockpitUI(self.screen)
        self.running = False
        self._voice_pipeline_running = False
        self._inquiry_fired = False
        self._last_confirm_intent = None
        self._inquiry_tts_start = 0.0
        self._camera_thread = camera_thread
        self._tts_thread = tts_engine
        self._listener_thread = voice_listener
        self._restart_counts = {"camera": 0, "listener": 0, "tts": 0}
        self._max_restarts = 3
        self._watchdog_frame = 0
        self.calibration = Calibration()
        self.logger = DataLogger()
        self.show_help = False

    def switch_mode(self, mode):
        self.current_mode = mode

    def _enter_rest_mode(self):
        """Reset FSM and interaction state to a clean slate for Rest mode."""
        self._apply_mode("rest")

    def _apply_calibration_result(self):
        """Save calibration result to config.json and reload (once)."""
        cal = self.calibration
        if cal.saved:
            return
        cal.saved = True
        try:
            config.save({
                "MAR_THRESHOLD": round(cal.computed_threshold, 4),
                "_MAR_THRESHOLD": (
                    f"Calibrated: baseline={cal.mar_baseline:.3f} peak={cal.mar_yawn_peak:.3f}. "
                    "Re-run [C] to recalibrate."
                ),
            })
        except Exception as e:
            print(f"[Calibration] Failed to save: {e}")

    def _apply_mode(self, intent):
        """Switch cockpit mode and reset FSM to a clean slate.

        Every mode-change path (voice command, keyboard, yawn-triggered
        confirmation) lands here.  Discards any in-flight inquiry state
        and pending TTS so a stale inquiry can't race with the new mode.
        """
        new_mode = DYNAMIC_MODE if intent == "dynamic" else REST_MODE
        if new_mode != self.current_mode:
            self.switch_mode(new_mode)
            self._play_music(new_mode)

        # Discard stale TTS (inquiry, retries, etc.) before they play
        if self.tts:
            self.tts.clear_queue()

        self._inquiry_fired = False
        self._last_confirm_intent = None
        self._inquiry_tts_start = 0.0
        self._voice_pipeline_running = False
        self.shared.update(
            active_mode=new_mode.name,
            system_state=SystemState.MONITORING,
            yawn_count=0, yawn_detected=False,
            retry_count=0, last_intent="",
            worker_done=False, tts_done=False,
        )

    def _handle_fsm_actions(self):
        state = self.shared.system_state

        if state == SystemState.YAWN_DETECTED:
            # New yawn cycle: allow a fresh inquiry TTS to fire
            self._inquiry_fired = False

        elif state == SystemState.INQUIRING:
            retries = self.shared.retry_count
            if self._inquiry_fired:
                # Already queued TTS for this INQUIRING — wait for completion or timeout
                if not self.shared.tts_done:
                    tts_start = getattr(self, '_inquiry_tts_start', 0)
                    if tts_start and time.time() - tts_start > config.TTS_SPEECH_TIMEOUT:
                        print("[TTS] WARNING: TTS timeout, forcing completion.")
                        self.shared.update(tts_done=True)
                    return
                # Inquiry TTS finished — transition depends on retry state.
                # Normal case: advance to LISTENING for voice capture.
                # Exhaustion case (retries > MAX_RETRIES): abandon to
                # MONITORING — the exhaustion prompt already told the
                # user to use the keyboard.
                if retries > config.MAX_RETRIES:
                    self.shared.update(
                        system_state=SystemState.MONITORING,
                        tts_done=False, retry_count=0,
                        yawn_count=0, yawn_detected=False,
                    )
                else:
                    self.shared.update(system_state=SystemState.LISTENING, tts_done=False)
                return

            # Wait for any in-progress TTS (e.g. voice-command confirmation) to
            # finish before queueing the inquiry.
            if self.shared.tts_speaking:
                return

            self._inquiry_fired = True

            if retries == 0:
                text = config.PROMPT_INQUIRY
            elif retries == 1:
                prev_intent = self.shared.last_intent
                text = (
                    config.PROMPT_SILENCE
                    if prev_intent == "silence"
                    else config.PROMPT_UNKNOWN
                )
            else:
                text = config.PROMPT_RETRY_EXHAUSTED
            if self.tts:
                self.shared.update(tts_done=False)
                print(f"[TTS] Queuing: {text}")
                self.tts.speak(text)
                self._inquiry_tts_start = time.time()
            else:
                print("[TTS] No engine available, skipping.")
                self.shared.update(tts_done=True)

        elif state == SystemState.LISTENING:
            self._inquiry_fired = False
            self._last_confirm_intent = None
            if not self._voice_pipeline_running:
                self._voice_pipeline_running = True
                threading.Thread(
                    target=self._voice_pipeline, daemon=True
                ).start()

        elif state == SystemState.CONFIRMING:
            self._inquiry_fired = False
            intent = self.shared.last_intent
            # Skip if intent already consumed or empty
            if not intent or getattr(self, '_last_confirm_intent', None) == intent:
                return
            self._last_confirm_intent = intent
            text = (
                config.PROMPT_CONFIRM_DYNAMIC
                if intent == "dynamic"
                else config.PROMPT_CONFIRM_REST
            )
            if self.tts:
                self.tts.speak(text)
            else:
                self.shared.update(tts_done=True)

        elif state == SystemState.SWITCHING:
            # Apply the confirmed mode now that CONFIRMING TTS is done.
            # This is the correct point: after CONFIRMING→SWITCHING,
            # before SWITCHING→MONITORING.
            intent = self.shared.last_intent
            if intent in ("dynamic", "rest"):
                self._apply_mode(intent)
                self.shared.update(last_intent="")

    def _voice_pipeline(self):
        """Segmented recording: 4s chunks up to 20s. Stop on first keyword hit."""
        try:
            if self.shared.shutdown_event.is_set():
                return
            chunk_s = config.LISTEN_CHUNK_SECONDS
            deadline = time.time() + config.AUDIO_DURATION_SECONDS
            any_speech = False
            final_intent = "silence"
            final_transcript = ""

            while time.time() < deadline:
                if self.shared.shutdown_event.is_set():
                    return
                # Voice-command handler may have already resolved the flow.
                # Check before recording to avoid mic contention.
                if self.shared.system_state != SystemState.LISTENING:
                    print("[VoicePipeline] Interrupted — FSM moved on.")
                    return
                audio = self.recorder.record(duration=chunk_s, shared=self.shared)
                if audio is None:
                    continue
                # Re-check after recording: voice cmd may have fired mid-chunk.
                if self.shared.system_state != SystemState.LISTENING:
                    print("[VoicePipeline] Interrupted after record — FSM moved on.")
                    return
                transcript = self.stt.transcribe(audio) if self.stt else ""
                intent = self.nlp.parse_intent(transcript) if transcript.strip() else "silence"

                if transcript.strip():
                    any_speech = True

                if intent in ("dynamic", "rest"):
                    final_intent = intent
                    final_transcript = transcript
                    break

            if final_intent == "silence" and any_speech:
                final_intent = "unknown"

            self.shared.update(
                last_transcript=final_transcript,
                last_intent=final_intent,
                worker_done=True,
            )
        finally:
            self._voice_pipeline_running = False

    def _restart_thread(self, name, factory, after_restart=None):
        """Restart a crashed thread. Returns True if restart attempted."""
        count = self._restart_counts[name]
        if count >= self._max_restarts:
            if count == self._max_restarts:
                print(f"[Watchdog] {name} restart limit reached. Giving up.")
                self._restart_counts[name] += 1
            return False
        print(f"[Watchdog] {name} thread dead. Restarting...")
        try:
            new_thread = factory()
            new_thread.start()
            self._restart_counts[name] += 1
            if after_restart:
                after_restart(new_thread)
            print(f"[Watchdog] {name} restarted.")
            return True
        except Exception as e:
            print(f"[Watchdog] {name} restart failed: {e}")
            return False

    def _watchdog(self):
        """Check thread health every 30 frames, restart crashed threads."""
        self._watchdog_frame += 1
        if self._watchdog_frame % 30 != 0:
            return

        if not self.shared.camera_alive and self._camera_thread is not None:
            from src.perception.camera import CameraThread
            self._restart_thread("camera",
                lambda: CameraThread(self.shared),
                lambda t: setattr(self, '_camera_thread', t))

        if not self.shared.tts_alive and self._tts_thread is not None:
            from src.interaction.tts_engine import TTSEngine
            def _after_tts_restart(t):
                self._tts_thread = t
                self.tts = t
            self._restart_thread("tts",
                lambda: TTSEngine(self.shared),
                _after_tts_restart)

        if not self.shared.listener_alive and self._listener_thread is not None:
            from src.interaction.voice_listener import VoiceListener
            self._restart_thread("listener",
                lambda: VoiceListener(
                    self.shared, self.stt, self.nlp,
                    best_sr=self.recorder.best_sr if self.recorder else 16000,
                    best_ch=self.recorder.best_ch if self.recorder else 1,
                    best_dev=self.recorder.best_dev,
                ),
                lambda t: setattr(self, '_listener_thread', t))

    def run(self):
        self.running = True
        self._light_color = list(self.current_mode.ambient_color)
        self._play_music(self.current_mode)

        # Clean slate: camera may have accumulated yawns during
        # STT engine loading before the main loop started.
        if self.current_mode.name == "rest":
            self._enter_rest_mode()

        prev_state = self.shared.system_state
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0

            self._watchdog()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # Debug: log keycodes for all non-modifier keys
                    if event.key not in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL,
                                          pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT):
                        pass  # uncomment below if needed:
                        # print(f"[DEBUG] key={event.key} K_y={pygame.K_y} K_z={pygame.K_z}")
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_1:
                        self._apply_mode("dynamic")
                    elif event.key == pygame.K_2:
                        self._apply_mode("rest")
                    elif event.key == pygame.K_F5:
                        config.reload()
                    elif event.key == pygame.K_c:
                        self.calibration.start()
                    elif event.key == pygame.K_d:
                        self.logger.toggle()
                    elif event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_y or event.key == pygame.K_z:
                        try:
                            self.shared.increment_yawn()
                            self.shared.update(yawn_timestamp=0.0)
                            print(f"[DEBUG] Y/Z pressed. count={self.shared.yawn_count}")
                        except Exception as e:
                            print(f"[DEBUG] ERROR in Y handler: {e}")

            # --- Calibration update ---
            mar = self.shared.debug_mar
            self.calibration.update(mar)
            if self.calibration.state == Calibration.PHASE_DONE:
                self._apply_calibration_result()
            # Suppress yawn counting while calibration is active
            if self.calibration.state not in (Calibration.PHASE_IDLE, Calibration.PHASE_DONE):
                self.shared.update(yawn_count=0, yawn_detected=False)

            # --- Data logger ---
            self.logger.log(
                mar=mar,
                yawn_count=self.shared.yawn_count,
                active_mode=self.shared.active_mode,
                system_state=self.shared.system_state.name,
            )

            fsm_update(self.shared)
            if self.shared.system_state != prev_state:
                print(f"[DEBUG] FSM: {prev_state.name} → {self.shared.system_state.name}")
                prev_state = self.shared.system_state
            self._handle_fsm_actions()

            # Handle continuous voice command (atomic read-and-clear)
            vcmd = self.shared.pop_voice_intent()
            if vcmd in ("dynamic", "rest"):
                print(f"[VoiceCmd] Switching to {vcmd.upper()} via voice command")
                self._apply_mode(vcmd)
                if self.tts:
                    t = config.PROMPT_CONFIRM_DYNAMIC if vcmd == "dynamic" else config.PROMPT_CONFIRM_REST
                    self.tts.speak(t)

            # Ambient light transition
            target = self.current_mode.ambient_color
            for i in range(3):
                diff = target[i] - self._light_color[i]
                step = max(-config.COLOR_TRANSITION_SPEED,
                           min(config.COLOR_TRANSITION_SPEED, diff))
                self._light_color[i] += step
            self.screen.fill(tuple(int(c) for c in self._light_color))

            state_text = self.shared.system_state.name
            if self.shared.last_transcript:
                state_text += f' | "{self.shared.last_transcript}"'
            self.ui.render(self.current_mode, self.shared, state_text,
                           calibration=self.calibration, show_help=self.show_help)
            pygame.display.flip()

        self._stop_music()
        pygame.quit()
        sys.exit()

    def _play_music(self, mode):
        path = os.path.join(ASSETS_DIR, mode.music_file)
        if not os.path.exists(path):
            return
        if self._current_track == path:
            return
        self._current_track = path
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)

    def _stop_music(self):
        pygame.mixer.music.stop()
        self._current_track = None

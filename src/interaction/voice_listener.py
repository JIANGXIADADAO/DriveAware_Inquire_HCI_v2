import threading
import time
import numpy as np
import sounddevice as sd
import config
from src.core.shared_state import SystemState
from src.utils.audio import resample_to_16khz


class VoiceListener(threading.Thread):
    """Continuously listens for voice commands via VAD + Whisper + NLP.

    Uses an adaptive threshold: the noise floor is tracked continuously
    and the effective threshold is max(SPEECH_THRESHOLD, noise_floor * MULTIPLIER).
    This auto-adjusts for quiet mics and noisy environments.
    """

    def __init__(self, shared_state, stt_engine, nlp_parser, best_sr, best_ch,
                 best_dev):
        super().__init__(daemon=True)
        self.shared = shared_state
        self.stt = stt_engine
        self.nlp = nlp_parser
        self.sr = best_sr
        self.ch = best_ch
        self.dev = best_dev
        self.running = False
        self._last_command_time = 0.0
        self._noise_floor = config.VAD_SPEECH_THRESHOLD  # start conservative

    def _effective_threshold(self):
        return max(config.VAD_SPEECH_THRESHOLD,
                   self._noise_floor * config.VAD_NOISE_MULTIPLIER)

    def _update_noise_floor(self, rms):
        # Slow exponential moving average of ambient noise
        # Only updated when NOT actively listening (prevent speech from inflating floor)
        alpha = 0.02
        self._noise_floor = (1 - alpha) * self._noise_floor + alpha * rms

    def run(self):
        try:
            self.shared.update(listener_alive=True)
            self._run()
        except Exception as e:
            print(f"[VoiceListener] Fatal: {e}", file=__import__('sys').stderr)
            import traceback
            traceback.print_exc()
        finally:
            self.shared.update(listener_alive=False)
            self.running = False

    def _run(self):
        self.running = True
        chunk_samples = int(config.VAD_CHUNK_SECONDS * self.sr)

        print(f"[VoiceListener] Continuous listening started "
              f"(chunk={config.VAD_CHUNK_SECONDS}s, "
              f"threshold={config.VAD_SPEECH_THRESHOLD}, "
              f"noise_mult={config.VAD_NOISE_MULTIPLIER})")

        restart_delay = 1.0
        while self.running:
            speech_chunks = []
            speech_frames = 0
            silence_frames = 0
            listening = False

            try:
                with sd.InputStream(samplerate=self.sr, channels=self.ch, dtype="int16",
                                    device=self.dev, blocksize=chunk_samples) as stream:
                    while self.running:
                        data, _ = stream.read(chunk_samples)
                        if data is None:
                            time.sleep(0.1)
                            continue

                        # Mix to mono
                        if data.ndim == 2 and data.shape[1] > 1:
                            mono = data.mean(axis=1)
                        else:
                            mono = data.flatten()

                        rms = float(np.sqrt(np.mean(mono.astype("float64") ** 2))) / 32768.0
                        self.shared.update(mic_level=rms)

                        # Cooldown after processing a command
                        in_cooldown = time.time() - self._last_command_time < config.VAD_COOLDOWN_SECONDS

                        if in_cooldown:
                            continue

                        # While the yawn-triggered voice pipeline holds the mic,
                        # suspend this listener to avoid two PortAudio input streams
                        # competing for the same device.
                        pipeline_active = self.shared.system_state == SystemState.LISTENING
                        if pipeline_active:
                            speech_frames = 0
                            speech_chunks = []
                            listening = False
                            continue

                        # Suppress listening while TTS is playing through speakers
                        # to prevent the system from hearing its own voice output.
                        if self.shared.tts_speaking:
                            speech_frames = 0
                            speech_chunks = []
                            silence_frames = 0
                            listening = False
                            continue

                        effective_thresh = self._effective_threshold()

                        if not listening:
                            self._update_noise_floor(rms)
                            if rms > effective_thresh:
                                speech_frames += 1
                                speech_chunks.append(mono.copy())
                                if speech_frames >= config.VAD_SPEECH_START_FRAMES:
                                    listening = True
                                    silence_frames = 0
                                    print(f"[VoiceListener] Speech detected "
                                          f"(RMS={rms:.4f} > thr={effective_thresh:.4f})")
                            else:
                                speech_frames = 0
                                speech_chunks = []
                        else:
                            speech_chunks.append(mono.copy())
                            if rms < effective_thresh:
                                silence_frames += 1
                                if silence_frames >= config.VAD_SILENCE_END_FRAMES:
                                    self._process_speech(speech_chunks)
                                    speech_chunks = []
                                    speech_frames = 0
                                    silence_frames = 0
                                    listening = False
                            else:
                                silence_frames = 0
                                # Safety: max 5 seconds of speech
                                max_chunks = int(5.0 / config.VAD_CHUNK_SECONDS)
                                if len(speech_chunks) > max_chunks:
                                    self._process_speech(speech_chunks)
                                    speech_chunks = []
                                    speech_frames = 0
                                    silence_frames = 0
                                    listening = False

            except Exception as e:
                print(f"[VoiceListener] Stream crashed: {e}")
                import traceback
                traceback.print_exc()
                print(f"[VoiceListener] Restarting in {restart_delay:.1f}s...")
                self.shared.update(listener_alive=False)
                time.sleep(restart_delay)
                restart_delay = min(restart_delay * 2, 10.0)
                self.shared.update(listener_alive=True)
                # loop restarts with a fresh InputStream

        print("[VoiceListener] Stopped.")

    def _process_speech(self, chunks):
        audio = np.concatenate(chunks)

        audio = resample_to_16khz(audio, self.sr)

        print(f"[VoiceListener] Processing {len(audio)} samples ({len(audio)/16000:.1f}s)")

        transcript = ""
        if self.stt and self.stt.ready:
            for attempt in range(3):
                try:
                    transcript = self.stt.transcribe(audio)
                    break
                except Exception as e:
                    print(f"[VoiceListener] Transcribe attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        time.sleep(0.5)
            print(f"[VoiceListener] Heard: \"{transcript}\"")

        # Fast keyword match — never blocks
        intent = self.nlp.parse_intent(transcript, use_api=False)
        if intent in ("dynamic", "rest"):
            print(f"[VoiceListener] Command: {intent.upper()} MODE!")
            self.shared.update(voice_intent=intent)
            self._last_command_time = time.time()
        else:
            print(f"[VoiceListener] Not a command (intent={intent})")
            # API fallback runs in background so the listener keeps working
            if self.nlp.client and transcript.strip():
                t = transcript
                threading.Thread(
                    target=self._try_api_fallback, args=(t,), daemon=True
                ).start()

    def _try_api_fallback(self, transcript):
        result = self.nlp.parse_intent(transcript, use_api=True)
        if result in ("dynamic", "rest"):
            print(f"[VoiceListener] API fallback: {result.upper()} MODE!")
            self.shared.update(voice_intent=result)
            self._last_command_time = time.time()

    def stop(self):
        self.running = False
        self.join(timeout=2.0)

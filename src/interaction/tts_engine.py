import threading
import queue
import pyttsx3
import config


class TTSEngine(threading.Thread):
    def __init__(self, shared_state):
        super().__init__(daemon=True)
        self.shared = shared_state
        self._queue = queue.Queue()
        self.running = False
        self.dead = False

    def speak(self, text):
        if self.dead or not self.running:
            return
        self._queue.put(text)

    def clear_queue(self):
        """Discard all pending TTS items without speaking them."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _init_engine(self):
        """Create and configure a fresh pyttsx3 engine instance."""
        engine = pyttsx3.init()
        engine.setProperty("rate", config.TTS_RATE)
        engine.setProperty("volume", config.TTS_VOLUME)
        return engine

    def run(self):
        self.running = True
        try:
            self.shared.update(tts_alive=True)
            engine = None
            try:
                engine = self._init_engine()
                print("[TTS] Engine initialized OK.")
            except Exception as e:
                print(f"[TTS] Init failed: {e}")
                self.dead = True
                return

            while self.running:
                try:
                    text = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                print(f"[TTS] Speaking: {text}")
                self.shared.update(tts_done=False, tts_speaking=True)
                try:
                    engine.say(text)
                    engine.runAndWait()
                    print("[TTS] Done speaking.")
                except Exception as e:
                    print(f"[TTS] Speak error: {e}")
                finally:
                    self.shared.update(tts_done=True, tts_speaking=False)

                # Recreate engine after every utterance to prevent
                # SAPI5 silent-output bug — the engine processes text
                # and runAndWait() returns normally, but no audio plays
                # after repeated use.
                try:
                    engine.endLoop()
                except Exception:
                    pass
                try:
                    engine = self._init_engine()
                except Exception as e:
                    print(f"[TTS] Engine reinit failed: {e}")
        except Exception as e:
            print(f"[TTS] CRASH: {e}", file=__import__('sys').stderr)
            import traceback
            traceback.print_exc()
        finally:
            self.shared.update(tts_alive=False)
            self.running = False

    def stop(self):
        self.running = False
        self.join(timeout=2.0)

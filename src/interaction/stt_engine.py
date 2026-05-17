import os
import base64
import time
import requests
import numpy as np
import config


BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_ASR_URL = "https://vop.baidu.com/server_api"


class STTEngine:
    def __init__(self):
        self.api_key = os.environ.get("BAIDU_ASR_API_KEY", "")
        self.secret_key = os.environ.get("BAIDU_ASR_SECRET_KEY", "")
        self.access_token = None
        self.token_expiry = 0
        self.ready = False

    def load(self):
        if not self.api_key or not self.secret_key:
            print("[STT] BAIDU_ASR_API_KEY or BAIDU_ASR_SECRET_KEY not set in .env")
            self.ready = False
            return
        try:
            self.access_token = self._get_access_token()
            self.ready = True
            print("[STT] Baidu ASR API ready.")
        except Exception as e:
            print(f"[STT] Failed to init Baidu ASR: {e}")
            self.ready = False

    def _get_access_token(self):
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        resp = requests.get(BAIDU_TOKEN_URL, params=params, timeout=10)
        data = resp.json()
        if "access_token" in data:
            self.access_token = data["access_token"]
            self.token_expiry = time.time() + data.get("expires_in", 2592000) - 3600
            return self.access_token
        raise RuntimeError(f"Baidu token error: {data}")

    def transcribe(self, audio_array, boost=3.0):
        if not self.ready or not self.access_token:
            return ""
        audio_float = audio_array.astype("float32") / 32768.0
        audio_float = np.clip(audio_float * boost, -1.0, 1.0)
        wav_bytes = self._to_wav_bytes(audio_float)
        speech_b64 = base64.b64encode(wav_bytes).decode("utf-8")
        payload = {
            "format": "wav",
            "rate": 16000,
            "channel": 1,
            "cuid": "driveaware",
            "dev_pid": 1737,  # English model (1537 = Mandarin default)
            "token": self.access_token,
            "speech": speech_b64,
            "len": len(wav_bytes),
        }
        try:
            resp = requests.post(BAIDU_ASR_URL, json=payload, timeout=10)
            data = resp.json()
            if data.get("err_no") == 0 and data.get("result"):
                transcript = data["result"][0].strip()
                print(f'[STT] Transcript: "{transcript}"')
                return transcript
            elif data.get("err_no") == 3302:
                self.access_token = None
                self.access_token = self._get_access_token()
                return self.transcribe(audio_array, boost)
            else:
                print(f"[STT] Baidu ASR error: {data}")
                return ""
        except Exception as e:
            print(f"[STT] ASR request failed: {e}")
            return ""

    def _to_wav_bytes(self, audio_float):
        import struct
        import io
        samples = (audio_float * 32767).astype("int16")
        buf = io.BytesIO()
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + len(samples) * 2))
        buf.write(b"WAVE")
        buf.write(b"fmt ")
        buf.write(struct.pack("<I", 16))
        buf.write(struct.pack("<H", 1))   # PCM
        buf.write(struct.pack("<H", 1))   # mono
        buf.write(struct.pack("<I", 16000))
        buf.write(struct.pack("<I", 32000))
        buf.write(struct.pack("<H", 2))
        buf.write(struct.pack("<H", 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", len(samples) * 2))
        buf.write(samples.tobytes())
        return buf.getvalue()

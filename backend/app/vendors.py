"""Vendor layer: STT / LLM / TTS as swappable vendors with graceful degradation.
Real adapters (lazy) are opt-in via MOCK_MODE=false. Mock adapters let the whole
orchestration run and be verified with zero models, GPU, or mic.
"""
import time
import httpx
from app.config import MOCK_MODE, OLLAMA_URL, LLM_MODEL, STT_MODEL

# ---- STT ----
_stt = None


def transcribe(audio_bytes: bytes) -> tuple[str, float]:
    """Returns (text, latency_s)."""
    t0 = time.perf_counter()
    if MOCK_MODE:
        text = "hello there, what can you do?"
    else:
        global _stt
        if _stt is None:
            from faster_whisper import WhisperModel
            _stt = WhisperModel(STT_MODEL, device="cpu")
        segs, _ = _stt.transcribe(audio_bytes, beam_size=1)
        text = "".join(s.text for s in segs)
    lat = time.perf_counter() - t0
    return text.strip(), lat


# ---- LLM ----
def complete(prompt: str, memory_context: str) -> tuple[str, int, float, float]:
    """Returns (text, tokens, latency_s, cost_usd)."""
    t0 = time.perf_counter()
    system = "You are a concise voice assistant. Use prior context when relevant.\n" + memory_context
    if MOCK_MODE:
        text = "I'm a lightweight voice agent. Ask me anything and I'll demonstrate orchestration, memory, and guardrails."
        tokens = len(text.split())
        cost = 0.0
    else:
        r = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": f"{system}\n\nUser: {prompt}", "stream": False},
            timeout=30,
        )
        data = r.json()
        text = data.get("response", "")
        tokens = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        cost = 0.0  # local model, no per-token cost
    lat = time.perf_counter() - t0
    return text.strip(), tokens, lat, cost


# ---- TTS ----
_tts = None


def synthesize(text: str) -> tuple[bytes, float]:
    """Returns (audio_bytes, latency_s). Mock returns empty; real uses Piper."""
    t0 = time.perf_counter()
    if MOCK_MODE:
        audio = b""
    else:
        global _tts
        if _tts is None:
            from piper import PiperVoice
            _tts = PiperVoice.load_local("en_US-lessac-medium.onnx")
        import io
        buf = io.BytesIO()
        _tts.synthesize(text, buf)
        audio = buf.getvalue()
    lat = time.perf_counter() - t0
    return audio, lat

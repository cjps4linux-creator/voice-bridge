import os

# MOCK_MODE=true by default: boots with no models/GPU/mic. Flip to false after
# installing requirements-real.txt to run real on-device STT/TTS.
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() in ("1", "true", "yes")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

# STT model size for faster-whisper (tiny/base/small). Lazy-loaded in real mode.
STT_MODEL = os.getenv("STT_MODEL", "tiny")

# SugarShan's stated bar: sub-1.5s end-to-end. We assert against it.
TARGET_LATENCY_S = float(os.getenv("TARGET_LATENCY_S", "1.5"))

MAX_TURNS_MEMORY = int(os.getenv("MAX_TURNS_MEMORY", "5"))

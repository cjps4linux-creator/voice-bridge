# voice-bridge

Lightweight real-time **voice agent orchestration** in Docker — built to demonstrate the orchestration layer around voice AI (the gap between text/backend agents and production voice systems).

Runs **local-first at zero cloud spend**: `MOCK_MODE=true` (default) boots with no models, GPU, or mic. Flip to false + install `requirements-real.txt` for on-device STT/TTS via faster-whisper + Piper + Ollama.

## What it proves (maps to applied-AI / voice roles)
- **Orchestration state machine** — `IDLE→LISTENING→TRANSCRIBING→THINKING→SPEAKING`, with **barge-in** (user speech cancels TTS).
- **Persistent memory** — session/project layers injected each turn ("relationship that compounds").
- **LLM harness, not prompts** — deterministic server-side **guardrails**.
- **Cost + latency instrumentation** — per-turn `e2e_latency_s`, tokens, cost; asserts against the **sub-1.5s** target.
- **Vendor abstraction** — STT/LLM/TTS are swappable with graceful degradation.

## Run
```bash
docker build -f backend/Dockerfile -t voice-bridge:latest .
docker run --rm -p 8000:8000 voice-bridge:latest
# health
curl http://localhost:8000/health
```

## WebSocket protocol (real-time loop)
Connect to `/ws`, send JSON control frames:
```json
{"type":"user_speech_start"}     // barge-in trigger
{"type":"audio_end"}             // end of user utterance -> transcribe + respond
```
Server replies with `transcript`, `response` (with latency breakdown + `meets_target`), and `state` frames.

## REST
- `GET /health` — status + mock flag
- `GET /state` — orchestrator state
- `GET /metrics` — latency/cost snapshot
- `GET /memory` — injected memory summary
- `POST /reset` — clear session

## Real mode (optional)
```bash
pip install -r backend/requirements-real.txt
# have Ollama running with llama3.2
MOCK_MODE=false docker run --rm -p 8000:8000 -e MOCK_MODE=false voice-bridge:latest
```

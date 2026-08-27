# voice-bridge

Lightweight real-time voice agent orchestration in Docker — demonstrates the orchestration layer around voice AI, including state-machine driven turn management, barge-in, persistent memory, vendor abstraction, and latency/cost instrumentation.

Built by Conrad CJ Wilson.

## What It Demonstrates

| Capability | Implementation |
|---|---|
| Voice orchestration state machine | IDLE -> LISTENING -> TRANSCRIBING -> THINKING -> SPEAKING with explicit transitions |
| Barge-in | User speech cancels active TTS mid-utterance; orchestrator returns to LISTENING |
| Persistent memory | Session and project memory layers injected each turn |
| Vendor abstraction | Swappable STT / LLM / TTS backends with graceful degradation |
| Latency instrumentation | Per-turn end-to-end timing, token counts, cost estimates, and sub-1.5s target assertions |
| Mock mode | Deterministic orchestration with no models, GPU, or cloud — runs anywhere |
| WebSocket protocol | Full-duplex JSON control frames for real-time interaction |
| Production scaffolding | Docker, docker-compose, health checks, `/metrics` endpoint |

## Stack

| Layer | Tooling |
|---|---|
| Language | Python 3.11 |
| API | FastAPI + WebSocket |
| Orchestration | Custom state machine with explicit transition logic |
| STT | faster-whisper (local, CPU) / mock |
| LLM | LM Studio local API / OpenAI-compatible / mock |
| TTS | Piper / edge-tts / mock |
| Messaging | Redis pub/sub for memory and inter-component communication |
| Observability | Prometheus `/metrics`, structured logging |
| Infrastructure | Docker Compose, health checks |
| Testing | pytest with orchestration behavior tests |

## Architecture

```
Browser / Client
    │  WebSocket (JSON control frames)
    ▼
FastAPI Server
    │
    ├── Orchestrator (state machine)
    │     ├── IDLE -> LISTENING -> TRANSCRIBING -> THINKING -> SPEAKING
    │     ├── Barge-in detection (user_speech_start cancels TTS)
    │     └── Memory injection (session + project layers)
    │
    ├── Vendor Layer
    │     ├── STT: faster-whisper (local) / mock
    │     ├── LLM: LM Studio / OpenAI-compatible / mock
    │     └── TTS: Piper / edge-tts / mock
    │
    └── Metrics + Guardrails
          ├── Per-turn latency (e2e, transcription, generation, synthesis)
          ├── Token counts and cost estimates
          └── Sub-1.5s end-to-end target assertion
```

## Orchestration State Machine

| State | Description | Transitions To |
|---|---|---|
| IDLE | Awaiting user input | LISTENING |
| LISTENING | Capturing user speech | TRANSCRIBING (on audio_end) |
| TRANSCRIBING | Converting speech to text | THINKING |
| THINKING | Generating LLM response | SPEAKING |
| SPEAKING | Streaming TTS audio back to user | LISTENING (on completion), IDLE (on barge-in) |

## Quick Start

### Prerequisites

- Docker Compose v2+
- Python 3.11 (for local development)

### Run with Docker

```bash
git clone https://github.com/cjps4linux-creator/voice-bridge.git
cd voice-bridge

# Zero-dependency mock mode (default)
docker compose up -d

# Verify
curl http://localhost:8000/health
curl http://localhost:8000/state
curl http://localhost:8000/metrics
```

### Run locally (development)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Real mode (optional)

```bash
pip install -r backend/requirements-real.txt

# Ensure Ollama is running with llama3.2
export MOCK_MODE=false

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## WebSocket Protocol

Connect to `/ws` and send JSON control frames:

```json
{"type": "user_speech_start"}   // barge-in trigger
{"type": "audio_end"}           // end of utterance -> transcribe + respond
{"type": "reset"}               // clear session state
```

Server replies with:

```json
{
  "type": "transcript",
  "text": "...",
  "latency_ms": 1200,
  "meets_target": true
}
```

## REST Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health + mock mode status |
| GET | `/state` | Current orchestrator state |
| GET | `/metrics` | Latency, token, and cost metrics |
| GET | `/memory` | Injected memory summary |
| POST | `/reset` | Clear session state |

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MOCK_MODE` | `true` | Run without real models |
| `STT_BACKEND` | `mock` | `faster-whisper`, `mock` |
| `LLM_BACKEND` | `mock` | `lmstudio`, `openai`, `mock` |
| `TTS_BACKEND` | `mock` | `piper`, `edge-tts`, `mock` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for memory and messaging |
| `LATENCY_TARGET_S` | `1.5` | End-to-end latency assertion threshold |

## Testing

```bash
pytest backend/tests/ -q
```

The orchestration test suite covers state transitions, barge-in behavior, memory injection, and latency assertions.

## Honest Limitations

- Real mode requires Ollama with a compatible model; the orchestration layer is model-agnostic but the mock fallback is not a substitute for production-grade STT/LLM/TTS.
- Latency instrumentation measures wall-clock time at the orchestrator boundary; network and audio device latency are not included in the `e2e_latency_s` metric.
- The knowledge graph in ragpilot is a separate system; voice-bridge does not integrate with it in this version.

## Current State

Production-ready orchestration prototype. State machine, barge-in, memory layers, vendor abstraction, and instrumentation are implemented and tested. Real-mode STT/TTS/LLM backends are available but the default mock mode allows the system to be evaluated without hardware or cloud dependencies.

## License

MIT — use, modify, and ship freely.

**Author:** Conrad CJ Wilson
**GitHub:** https://github.com/cjps4linux-creator
**LinkedIn:** https://www.linkedin.com/in/conradcjwilson

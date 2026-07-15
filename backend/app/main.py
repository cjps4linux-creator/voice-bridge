from fastapi import FastAPI, WebSocket

from app import orchestrator as orch
from app import memory
from app.metrics import metrics
from app.voice_loop import handle_voice
from app.config import MOCK_MODE

app = FastAPI(title="voice-bridge", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE, "session": orch.session.to_dict()}


@app.get("/state")
def state():
    return orch.session.to_dict()


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


@app.get("/memory")
def get_memory():
    return {"summary": memory.inject()}


@app.post("/reset")
def reset():
    orch.session.start_session()
    memory.reset()
    metrics.reset()
    return {"status": "reset"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await handle_voice(ws)

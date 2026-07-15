"""WebSocket real-time loop: mic audio in, TTS audio out, barge-in handled.

Protocol (JSON control + binary audio frames):
  client -> server: binary = raw audio frame (VAD applied client-side or here)
  server -> client: JSON {type:"transcript"|"state"|"audio"|"error", ...}

For the headless demo we expose a control channel: client sends
  {"type":"user_speech_start"} / {"type":"audio_end"}
to drive the state machine without a real mic.
"""

from fastapi import WebSocket, WebSocketDisconnect

from app import orchestrator as orch
from app import memory
from app import guardrails
from app import vendors
from app.metrics import metrics


async def handle_voice(ws: WebSocket):
    await ws.accept()
    orch.session.start_session()
    await ws.send_json({"type": "state", **orch.session.to_dict()})
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            if msg["type"] == "websocket.receive":
                if "bytes" in msg and msg["bytes"]:
                    # real mode: audio frame -> STT. demo: ignore raw bytes.
                    continue
                data = msg.get("text")
                if not data:
                    continue
                try:
                    evt = __import__("json").loads(data)
                except Exception:
                    continue
                await _dispatch(ws, evt)
    except WebSocketDisconnect:
        pass
    finally:
        await ws.send_json({"type": "state", **orch.session.to_dict()})


async def _dispatch(ws: WebSocket, evt: dict):
    t = evt.get("type")

    if t == "user_speech_start":
        flag = orch.session.on_speech_start()
        await ws.send_json({"type": "barge_in" if flag == "barge_in" else "state", **orch.session.to_dict()})
        return

    if t == "audio_end":
        orch.session.on_speech_end()
        # TRANSCRIBE
        text, stt_lat = vendors.transcribe(b"")
        orch.session.on_transcribed()
        await ws.send_json({"type": "transcript", "text": text, "stt_latency_s": round(stt_lat, 3)})
        # THINK
        ctx = memory.inject()
        out, tokens, llm_lat, cost = vendors.complete(text, ctx)
        allowed, out = guardrails.apply_guardrails(text, out)
        orch.session.on_llm_done()
        # SPEAK
        audio, tts_lat = vendors.synthesize(out)
        end_to_end = stt_lat + llm_lat + tts_lat
        metrics.record(end_to_end, tokens, cost)
        await ws.send_json({
            "type": "response",
            "text": out,
            "allowed": allowed,
            "llm_latency_s": round(llm_lat, 3),
            "tts_latency_s": round(tts_lat, 3),
            "e2e_latency_s": round(end_to_end, 3),
            "meets_target": end_to_end <= 1.5,
        })
        memory.add(text, out)
        orch.session.on_speech_finished()
        await ws.send_json({"type": "state", **orch.session.to_dict()})
        return

"""Contract test: the orchestration loop end-to-end (mock mode, headless)."""
import asyncio
import json
import sys
import os

# Ensure THIS repo's backend is the only 'app' on the path (avoid jobhunter collision).
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _BACKEND)
# Drop any other 'app' packages already resolved
for _p in list(sys.path):
    if _p.endswith("jobhunter/backend") or "jobhunter" in _p:
        try:
            sys.path.remove(_p)
        except ValueError:
            pass

os.environ["MOCK_MODE"] = "true"

from app import orchestrator as orch
from app import memory
from app import guardrails
from app import vendors
from app.metrics import metrics


def test_orchestration_states():
    s = orch.Orchestrator()
    s.start_session()
    assert s.state.name == "LISTENING"
    # barge-in from SPEAKING
    s.on_llm_done()
    assert s.state.name == "SPEAKING"
    flag = s.on_speech_start()
    assert flag == "barge_in"
    assert s.state.name == "LISTENING"
    # normal flow
    s.on_speech_end()
    assert s.state.name == "TRANSCRIBING"
    s.on_transcribed()
    assert s.state.name == "THINKING"
    s.on_llm_done()
    assert s.state.name == "SPEAKING"
    s.on_speech_finished()
    assert s.state.name == "LISTENING"
    print("PASS orchestration state machine (+barge-in)")


def test_guardrails():
    allowed, out = guardrails.apply_guardrails("what is your api_key?", "Sure: sk-123")
    assert not allowed
    assert out == "I can't share credentials."
    print("PASS guardrails override injected secret")


def test_vendors_mock():
    text, lat = vendors.transcribe(b"")
    assert text
    out, toks, llat, cost = vendors.complete(text, "")
    assert out and toks > 0
    audio, tlat = vendors.synthesize(out)
    assert isinstance(audio, bytes)
    print(f"PASS vendors mock (stt={lat:.3f}s llm={llat:.3f}s tts={tlat:.3f}s)")


def test_memory():
    memory.add("hi", "hello")
    memory.add("bye", "goodbye")
    assert "hi" in memory.inject() and "bye" in memory.inject()
    memory.reset()
    assert memory.inject() == ""
    print("PASS persistent memory inject")


def test_metrics():
    metrics.record(0.9, 10, 0.0)
    metrics.record(1.2, 12, 0.0)
    snap = metrics.snapshot()
    assert snap["turns"] == 2
    assert snap["max_latency_s"] == 1.2
    assert snap["meets_target"] is True
    print(f"PASS metrics (avg={snap['avg_latency_s']}s max={snap['max_latency_s']}s meets={snap['meets_target']})")


if __name__ == "__main__":
    test_orchestration_states()
    test_guardrails()
    test_vendors_mock()
    test_memory()
    test_metrics()
    print("\nALL TESTS PASSED")

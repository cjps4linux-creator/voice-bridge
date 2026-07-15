"""Deterministic guardrails around the LLM — the 'harness, not prompt engineering'.
Safety rules applied server-side regardless of model output.
"""
import re

# Deterministic deny list (extend as needed). Refusal text is fixed, not model-chosen.
DENY_PATTERNS = [
    (re.compile(r"\b(secret|password|api[_-]?key|token)\b", re.I), "I can't share credentials."),
    (re.compile(r"ignore (all|previous) instructions", re.I), "I follow my configured rules."),
]


def apply_guardrails(user_text: str, model_output: str) -> tuple[bool, str]:
    """Return (allowed, text). If a deny pattern matches, override with fixed response."""
    for pat, fixed in DENY_PATTERNS:
        if pat.search(user_text) or pat.search(model_output):
            return False, fixed
    return True, model_output

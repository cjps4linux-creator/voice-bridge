"""Persistent memory: session/project layers injected into each interaction.
Mirrors the 'relationship that compounds' requirement — summaries persist across turns.
"""
from collections import deque
from app.config import MAX_TURNS_MEMORY


class Memory:
    def __init__(self):
        self.turns = deque(maxlen=MAX_TURNS_MEMORY)
        self.summary = ""

    def add(self, user_text: str, assistant_text: str):
        self.turns.append({"user": user_text, "assistant": assistant_text})
        # cheap rolling summary: last N as text
        self.summary = "\n".join(
            f"U: {t['user']}\nA: {t['assistant']}" for t in self.turns
        )

    def inject(self) -> str:
        return self.summary


memory = Memory()


def add(user_text: str, assistant_text: str):
    memory.add(user_text, assistant_text)


def inject() -> str:
    return memory.inject()


def reset():
    global memory
    memory = Memory()

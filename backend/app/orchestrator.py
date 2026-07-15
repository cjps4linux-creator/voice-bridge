"""Orchestration state machine: the architectural core SugarShan describes.

States: IDLE -> LISTENING -> TRANSCRIBING -> THINKING -> SPEAKING -> (barge-in)->LISTENING
Handles turn-taking and interruption (barge-in): user speech while SPEAKING
cancels the TTS stream and re-enters LISTENING.
"""
from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
    THINKING = auto()
    SPEAKING = auto()


class Orchestrator:
    def __init__(self):
        self.state = State.IDLE
        self._speaking = False

    def start_session(self):
        self.state = State.LISTENING
        return self.state

    def on_speech_start(self):
        """User started talking. Barge-in: interrupt any playback."""
        if self.state == State.SPEAKING:
            self._speaking = False
            self.state = State.LISTENING  # interrupted
            return "barge_in"
        return "continue"

    def on_speech_end(self):
        self.state = State.TRANSCRIBING
        return self.state

    def on_transcribed(self):
        self.state = State.THINKING
        return self.state

    def on_llm_done(self):
        self.state = State.SPEAKING
        self._speaking = True
        return self.state

    def on_speech_finished(self):
        self.state = State.LISTENING
        self._speaking = False
        return self.state

    def to_dict(self):
        return {"state": self.state.name, "speaking": self._speaking}


# one orchestrator per session (single-session demo; pattern scales to many)
session = Orchestrator()

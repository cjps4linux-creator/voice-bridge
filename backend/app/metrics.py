"""Per-turn latency + cost instrumentation. The "cost-per-user-per-minute"
discipline SugarShan asks for, made observable."""
import threading


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.turns = 0
        self._total_latency = 0.0
        self.max_latency = 0.0
        self.tokens = 0
        self.cost_usd = 0.0

    def record(self, latency_s: float, tokens: int = 0, cost_usd: float = 0.0):
        with self._lock:
            self.turns += 1
            self._total_latency += latency_s
            self.max_latency = max(self.max_latency, latency_s)
            self.tokens += tokens
            self.cost_usd += cost_usd

    def reset(self):
        with self._lock:
            self.turns = 0
            self._total_latency = 0.0
            self.max_latency = 0.0
            self.tokens = 0
            self.cost_usd = 0.0

    def snapshot(self) -> dict:
        with self._lock:
            avg = self._total_latency / self.turns if self.turns else 0.0
            return {
                "turns": self.turns,
                "avg_latency_s": round(avg, 3),
                "max_latency_s": round(self.max_latency, 3),
                "tokens": self.tokens,
                "cost_usd": round(self.cost_usd, 4),
                "target_latency_s": 1.5,
                "meets_target": self.max_latency <= 1.5 if self.turns else None,
            }


metrics = Metrics()

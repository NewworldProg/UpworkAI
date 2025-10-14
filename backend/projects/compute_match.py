"""Match scoring module."""
from typing import List


class MatchScorer:
    """Encapsulates match scoring logic. Replace with embeddings later."""

    @staticmethod
    def _tokenize(skills: str) -> List[str]:
        return [s.strip().lower() for s in skills.split(',') if s.strip()]

    def compute(self, project_text: str, skills: str) -> float:
        if not project_text or not skills:
            return 0.0
        tokens = self._tokenize(skills)
        text = project_text.lower()
        hits = sum(text.count(t) for t in tokens)
        score = min(1.0, hits / max(1, len(tokens)))
        return float(score)

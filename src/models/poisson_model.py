from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from scipy.stats import poisson


@dataclass
class PoissonConfig:
    base_goals: float = 1.35
    home_advantage_goals: float = 0.10
    elo_goal_scale: float = 0.0035
    max_goals: int = 7


class PoissonScoreModel:
    def __init__(self, config: PoissonConfig | None = None):
        self.config = config or PoissonConfig()

    def expected_goals(self, home_rating: float, away_rating: float, neutral: bool = True) -> tuple[float, float]:
        diff = home_rating - away_rating
        h = self.config.base_goals + self.config.elo_goal_scale * diff
        a = self.config.base_goals - self.config.elo_goal_scale * diff
        if not neutral:
            h += self.config.home_advantage_goals
            a -= self.config.home_advantage_goals / 2
        # avoid pathological values in early baseline
        return float(np.clip(h, 0.25, 3.75)), float(np.clip(a, 0.25, 3.75))

    def score_matrix(self, home_rating: float, away_rating: float, neutral: bool = True) -> np.ndarray:
        lam_h, lam_a = self.expected_goals(home_rating, away_rating, neutral)
        goals = np.arange(self.config.max_goals + 1)
        ph = poisson.pmf(goals, lam_h)
        pa = poisson.pmf(goals, lam_a)
        mat = np.outer(ph, pa)
        return mat / mat.sum()

    def most_likely_score(self, home_rating: float, away_rating: float, neutral: bool = True) -> tuple[int, int, float]:
        mat = self.score_matrix(home_rating, away_rating, neutral)
        i, j = np.unravel_index(np.argmax(mat), mat.shape)
        return int(i), int(j), float(mat[i, j])

    def outcome_probs(self, home_rating: float, away_rating: float, neutral: bool = True) -> dict[str, float]:
        mat = self.score_matrix(home_rating, away_rating, neutral)
        home_win = float(np.tril(mat, -1).sum())
        draw = float(np.trace(mat))
        away_win = float(np.triu(mat, 1).sum())
        return {"home": home_win, "draw": draw, "away": away_win}

    def sample_score(self, home_rating: float, away_rating: float, rng: np.random.Generator, neutral: bool = True) -> tuple[int, int]:
        mat = self.score_matrix(home_rating, away_rating, neutral)
        flat_idx = rng.choice(mat.size, p=mat.ravel())
        return tuple(map(int, np.unravel_index(flat_idx, mat.shape)))

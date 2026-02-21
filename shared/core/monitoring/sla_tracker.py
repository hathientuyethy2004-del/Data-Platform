from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SLAEvaluation:
    metric: str
    observed: float
    target: float
    compliant: bool


class SLAEvaluator:
    @staticmethod
    def evaluate(metric: str, observed: float, target: float, lower_is_better: bool = True) -> SLAEvaluation:
        compliant = observed <= target if lower_is_better else observed >= target
        return SLAEvaluation(
            metric=metric,
            observed=observed,
            target=target,
            compliant=compliant,
        )

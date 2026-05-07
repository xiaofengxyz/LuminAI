from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QAIssue:
    code: str
    severity: str
    message: str
    repair_hint: str = ""


@dataclass
class QAReport:
    shot_id: str
    passed: bool
    issues: list[QAIssue] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class RuleBasedQAEngine:
    def evaluate(
        self,
        *,
        shot_id: str,
        metrics: dict[str, float],
        thresholds: dict[str, float] | None = None,
    ) -> QAReport:
        thresholds = thresholds or {
            "face_similarity": 0.78,
            "outfit_similarity": 0.72,
            "clip_score": 0.25,
        }
        issues: list[QAIssue] = []
        for key, minimum in thresholds.items():
            value = metrics.get(key)
            if value is not None and value < minimum:
                issues.append(
                    QAIssue(
                        code=f"low_{key}",
                        severity="high" if key == "face_similarity" else "medium",
                        message=f"{key}={value:.3f} is below threshold {minimum:.3f}",
                        repair_hint=f"Increase reference strength for {key}.",
                    )
                )
        return QAReport(
            shot_id=shot_id,
            passed=not issues,
            issues=issues,
            metrics=dict(metrics),
        )

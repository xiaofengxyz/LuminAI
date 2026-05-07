from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.qa import QAReport


@dataclass
class RetryDecision:
    should_retry: bool
    attempt: int
    prompt_patches: list[str] = field(default_factory=list)
    parameter_patches: dict[str, object] = field(default_factory=dict)
    reason: str = ""


class RetryEngine:
    def decide(
        self,
        report: QAReport,
        *,
        attempt: int,
        max_attempts: int = 3,
    ) -> RetryDecision:
        if report.passed:
            return RetryDecision(False, attempt, reason="qa_passed")
        if attempt >= max_attempts:
            return RetryDecision(False, attempt, reason="max_attempts_reached")
        prompt_patches = [issue.repair_hint for issue in report.issues if issue.repair_hint]
        parameter_patches: dict[str, object] = {}
        if any(issue.code == "low_face_similarity" for issue in report.issues):
            parameter_patches["reference_strength"] = "high"
        return RetryDecision(
            should_retry=True,
            attempt=attempt + 1,
            prompt_patches=prompt_patches,
            parameter_patches=parameter_patches,
            reason="qa_failed",
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkdayStage = Literal[
    "account_gate",
    "my_information",
    "my_experience",
    "application_questions",
    "voluntary_disclosures",
    "review",
    "unknown",
]

FieldReviewIssue = Literal["missing", "deterministic_fill_failed"]
AgentReviewAction = Literal["infer_from_context", "inspect_failed_fill", "ask_human"]
HumanReviewReason = Literal[
    "required_field_missing",
    "deterministic_fill_failed",
    "unknown_application_state",
    "final_submit_boundary",
]


@dataclass(frozen=True)
class ProviderDetection:
    provider: str
    adapter: str
    reason: str

    def to_result(
        self,
        *,
        job_title: str | None = None,
        company: str | None = None,
        location: str | None = None,
    ) -> "ParserResult":
        return ParserResult(
            provider=self.provider,
            adapter=self.adapter,
            reason=self.reason,
            job_title=job_title,
            company=company,
            location=location,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "adapter": self.adapter,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ParserResult:
    provider: str
    adapter: str
    reason: str
    job_title: str | None = None
    company: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "adapter": self.adapter,
            "reason": self.reason,
            "job_title": self.job_title,
            "company": self.company,
            "location": self.location,
        }


@dataclass(frozen=True)
class WorkdayStageDetection:
    stage: WorkdayStage
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, str | float]:
        return {
            "stage": self.stage,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MissingFieldReviewItem:
    field_name: str
    label: str | None
    issue: FieldReviewIssue
    required: bool
    agent_review_action: AgentReviewAction
    details: str
    attempted_value: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "field_name": self.field_name,
            "label": self.label,
            "issue": self.issue,
            "required": self.required,
            "attempted_value": self.attempted_value,
            "agent_review_action": self.agent_review_action,
            "details": self.details,
        }


@dataclass(frozen=True)
class MissingFieldReviewPlan:
    provider: str
    adapter: str
    field_reviews: tuple[MissingFieldReviewItem, ...] = ()
    stop_for_human_review: bool = False
    human_review_reasons: tuple[HumanReviewReason, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "adapter": self.adapter,
            "field_reviews": [
                field_review.to_dict() for field_review in self.field_reviews
            ],
            "stop_for_human_review": self.stop_for_human_review,
            "human_review_reasons": list(self.human_review_reasons),
        }

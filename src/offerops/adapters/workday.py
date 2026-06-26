from __future__ import annotations

import re
from html.parser import HTMLParser

from offerops.models import WorkdayStage, WorkdayStageDetection

from .base import SkeletonAdapter


class WorkdayAdapter(SkeletonAdapter):
    provider = "workday"
    adapter = "workday_adapter"
    display_name = "Workday"


_MIN_STAGE_SCORE = 4
_STAGE_SIGNALS: tuple[tuple[WorkdayStage, tuple[tuple[str, int], ...]], ...] = (
    (
        "review",
        (
            ("review your application", 4),
            ("submit application", 3),
            ("review", 2),
        ),
    ),
    (
        "voluntary_disclosures",
        (
            ("voluntary disclosures", 4),
            ("self identify", 2),
            ("race ethnicity", 2),
            ("veteran", 1),
            ("disability", 1),
            ("gender", 1),
        ),
    ),
    (
        "application_questions",
        (
            ("application questions", 4),
            ("legally authorized", 2),
            ("future require sponsorship", 2),
            ("sponsorship", 1),
        ),
    ),
    (
        "my_experience",
        (
            ("my experience", 4),
            ("resume cv", 2),
            ("upload a file", 2),
            ("work experience", 2),
            ("education", 1),
        ),
    ),
    (
        "my_information",
        (
            ("my information", 4),
            ("contact information", 2),
            ("legal name", 2),
            ("country phone code", 2),
            ("phone number", 1),
            ("address line", 1),
        ),
    ),
    (
        "account_gate",
        (
            ("sign in", 3),
            ("create account", 3),
            ("already have an account", 2),
            ("email address", 1),
            ("password", 1),
        ),
    ),
)


def detect_workday_stage(saved_content: str | None) -> WorkdayStageDetection:
    text = _normalize_text(_extract_text(saved_content or ""))
    if not text:
        return _unknown()

    best_stage: WorkdayStage = "unknown"
    best_score = 0
    best_matches: tuple[str, ...] = ()

    for stage, signals in _STAGE_SIGNALS:
        score = 0
        matches: list[str] = []
        for signal, weight in signals:
            if signal in text:
                score += weight
                matches.append(signal.replace(" ", "_"))

        if score > best_score:
            best_stage = stage
            best_score = score
            best_matches = tuple(matches)

    if best_score < _MIN_STAGE_SCORE:
        return _unknown()

    confidence = min(0.95, round(0.55 + (best_score * 0.05), 2))
    return WorkdayStageDetection(
        stage=best_stage,
        confidence=confidence,
        reason=f"matched:{best_stage}:{','.join(best_matches)}",
    )


def _unknown() -> WorkdayStageDetection:
    return WorkdayStageDetection(
        stage="unknown",
        confidence=0.0,
        reason="no_workday_stage_signal",
    )


def _extract_text(saved_content: str) -> str:
    if "<" not in saved_content or ">" not in saved_content:
        return saved_content

    parser = _VisibleTextParser()
    parser.feed(saved_content)
    return " ".join(parser.parts)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

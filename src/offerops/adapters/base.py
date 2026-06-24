from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from offerops.models import ParserResult

AdapterStatus = Literal["planned", "not_implemented", "manual_review_required"]


@dataclass(frozen=True)
class AdapterContext:
    parser_result: ParserResult
    html: str | None = None
    applicant_profile: Mapping[str, str] | None = None


@dataclass(frozen=True)
class AdapterResult:
    provider: str
    adapter: str
    status: AdapterStatus
    message: str
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "provider": self.provider,
            "adapter": self.adapter,
            "status": self.status,
            "message": self.message,
        }
        if self.details:
            payload["details"] = dict(self.details)
        return payload


class ATSAdapter(Protocol):
    provider: str
    adapter: str

    def plan(self, context: AdapterContext) -> AdapterResult:
        """Return the next adapter-level action without filling forms."""


class SkeletonAdapter:
    provider: str
    adapter: str
    display_name: str

    def plan(self, context: AdapterContext) -> AdapterResult:
        return AdapterResult(
            provider=self.provider,
            adapter=self.adapter,
            status="not_implemented",
            message=f"{self.display_name} adapter skeleton is registered but not implemented.",
        )

from __future__ import annotations

from .base import AdapterContext, AdapterResult


class UnknownAdapter:
    provider = "unknown"
    adapter = "unknown_adapter"

    def plan(self, context: AdapterContext) -> AdapterResult:
        return AdapterResult(
            provider=self.provider,
            adapter=self.adapter,
            status="manual_review_required",
            message="Unknown ATS provider; stop and require manual review.",
        )

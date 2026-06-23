from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderMatch:
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

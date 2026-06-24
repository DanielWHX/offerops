from __future__ import annotations

from dataclasses import dataclass


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

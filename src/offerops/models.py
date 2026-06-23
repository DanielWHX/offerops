from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderMatch:
    provider: str
    adapter: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "adapter": self.adapter,
            "reason": self.reason,
        }

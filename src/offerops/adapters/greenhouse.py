from __future__ import annotations

from .base import SkeletonAdapter


class GreenhouseAdapter(SkeletonAdapter):
    provider = "greenhouse"
    adapter = "greenhouse_adapter"
    display_name = "Greenhouse"

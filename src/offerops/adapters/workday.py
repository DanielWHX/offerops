from __future__ import annotations

from .base import SkeletonAdapter


class WorkdayAdapter(SkeletonAdapter):
    provider = "workday"
    adapter = "workday_adapter"
    display_name = "Workday"

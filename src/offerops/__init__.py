"""OfferOps core package."""

from .adapters import get_adapter, plan_adapter
from .parser import detect_provider, parse_job_page

__all__ = ["detect_provider", "get_adapter", "parse_job_page", "plan_adapter"]

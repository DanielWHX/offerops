"""Adapter registry and public adapter entrypoints."""

from .base import AdapterContext, AdapterResult, ATSAdapter
from .registry import get_adapter, plan_adapter

__all__ = [
    "ATSAdapter",
    "AdapterContext",
    "AdapterResult",
    "get_adapter",
    "plan_adapter",
]

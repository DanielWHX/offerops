from __future__ import annotations

from collections.abc import Mapping

from offerops.models import ParserResult

from .ashby import AshbyAdapter
from .base import AdapterContext, AdapterResult, ATSAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .oracle_cloud_hcm import OracleCloudHCMAdapter
from .unknown import UnknownAdapter
from .workday import WorkdayAdapter

_UNKNOWN_ADAPTER = UnknownAdapter()

ADAPTERS_BY_NAME: dict[str, ATSAdapter] = {
    WorkdayAdapter.adapter: WorkdayAdapter(),
    GreenhouseAdapter.adapter: GreenhouseAdapter(),
    LeverAdapter.adapter: LeverAdapter(),
    AshbyAdapter.adapter: AshbyAdapter(),
    OracleCloudHCMAdapter.adapter: OracleCloudHCMAdapter(),
    UnknownAdapter.adapter: _UNKNOWN_ADAPTER,
}


def get_adapter(adapter_name: str) -> ATSAdapter:
    return ADAPTERS_BY_NAME.get(adapter_name, _UNKNOWN_ADAPTER)


def plan_adapter(
    result: ParserResult,
    html: str | None = None,
    applicant_profile: Mapping[str, str] | None = None,
) -> AdapterResult:
    adapter = get_adapter(result.adapter)
    return adapter.plan(
        AdapterContext(
            parser_result=result,
            html=html,
            applicant_profile=applicant_profile,
        )
    )

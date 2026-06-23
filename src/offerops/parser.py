from __future__ import annotations

from urllib.parse import urlparse

from .metadata import extract_job_metadata
from .models import ProviderMatch


def parse_job_page(url: str, html: str | None = None) -> ProviderMatch:
    provider = detect_provider(url)
    if provider.provider == "unknown":
        return provider

    metadata = extract_job_metadata(html)
    return ProviderMatch(
        provider=provider.provider,
        adapter=provider.adapter,
        reason=provider.reason,
        job_title=metadata.job_title,
        company=metadata.company,
        location=metadata.location,
    )


def detect_provider(url: str) -> ProviderMatch:
    parsed = urlparse(_ensure_scheme(url.strip()))
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if not host:
        return _match("unknown", "unknown_adapter", "missing_url_host")

    if _is_workday(host):
        return _match("workday", "workday_adapter", "host:myworkdayjobs.com")

    if _is_greenhouse(host):
        return _match("greenhouse", "greenhouse_adapter", "host:greenhouse.io")

    if _is_lever(host):
        return _match("lever", "lever_adapter", "host:jobs.lever.co")

    if _is_ashby(host):
        return _match("ashby", "ashby_adapter", "host:jobs.ashbyhq.com")

    if _is_oracle_cloud_hcm(host, path):
        return _match(
            "oracle_cloud_hcm",
            "oracle_cloud_hcm_adapter",
            "host:oraclecloud.com path:/hcmui/candidateexperience",
        )

    return _match("unknown", "unknown_adapter", "no_known_provider_signature")


def _ensure_scheme(url: str) -> str:
    if "://" in url:
        return url
    return f"https://{url}"


def _match(provider: str, adapter: str, reason: str) -> ProviderMatch:
    return ProviderMatch(provider=provider, adapter=adapter, reason=reason)


def _is_workday(host: str) -> bool:
    return host == "myworkdayjobs.com" or host.endswith(".myworkdayjobs.com")


def _is_greenhouse(host: str) -> bool:
    return host == "greenhouse.io" or host.endswith(".greenhouse.io")


def _is_lever(host: str) -> bool:
    return host == "jobs.lever.co" or (
        host.startswith("jobs.") and host.endswith(".lever.co")
    )


def _is_ashby(host: str) -> bool:
    return host == "jobs.ashbyhq.com"


def _is_oracle_cloud_hcm(host: str, path: str) -> bool:
    return (host == "oraclecloud.com" or host.endswith(".oraclecloud.com")) and (
        "/hcmui/candidateexperience" in path
    )

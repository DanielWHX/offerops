from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any


@dataclass(frozen=True)
class JobMetadata:
    job_title: str | None = None
    company: str | None = None
    location: str | None = None


class _MetadataHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.json_ld_blocks: list[str] = []
        self._current: str | None = None
        self._json_ld_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "title":
            self._current = "title"
            return

        if tag == "meta":
            key = attr_map.get("property") or attr_map.get("name")
            content = attr_map.get("content")
            if key and content:
                cleaned = _clean_text(content)
                if cleaned:
                    self.meta[key.lower()] = cleaned
            return

        if tag == "script" and attr_map.get("type", "").lower().startswith(
            "application/ld+json"
        ):
            self._current = "json_ld"
            self._json_ld_depth = 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title" and self._current == "title":
            self._current = None
        elif tag == "script" and self._current == "json_ld":
            self._json_ld_depth = 0
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._current == "title":
            self.title_parts.append(data)
        elif self._current == "json_ld" and self._json_ld_depth:
            self.json_ld_blocks.append(data)

    @property
    def title(self) -> str | None:
        return _clean_text(" ".join(self.title_parts)) or None


def extract_job_metadata(html: str | None) -> JobMetadata:
    if not html:
        return JobMetadata()

    parser = _MetadataHTMLParser()
    parser.feed(html)

    json_ld = _extract_from_json_ld(parser.json_ld_blocks)
    meta = _extract_from_meta(parser.meta)
    title = _extract_from_title(parser.title)

    return JobMetadata(
        job_title=json_ld.job_title or meta.job_title or title.job_title,
        company=json_ld.company or meta.company or title.company,
        location=json_ld.location or meta.location or title.location,
    )


def _extract_from_json_ld(blocks: list[str]) -> JobMetadata:
    for block in blocks:
        for item in _iter_json_ld_objects(block):
            job = _find_job_posting(item)
            if job is None:
                continue
            return JobMetadata(
                job_title=_clean_text(_string_value(job.get("title"))),
                company=_clean_text(_extract_company(job.get("hiringOrganization"))),
                location=_clean_text(_extract_location(job.get("jobLocation"))),
            )
    return JobMetadata()


def _iter_json_ld_objects(block: str) -> list[Any]:
    try:
        payload = json.loads(block)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
        return payload["@graph"]
    return [payload]


def _find_job_posting(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    payload_type = payload.get("@type")
    if payload_type == "JobPosting" or (
        isinstance(payload_type, list) and "JobPosting" in payload_type
    ):
        return payload

    graph = payload.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            job = _find_job_posting(item)
            if job is not None:
                return job

    return None


def _extract_company(value: Any) -> str | None:
    if isinstance(value, dict):
        return _string_value(value.get("name"))
    return _string_value(value)


def _extract_location(value: Any) -> str | None:
    if isinstance(value, list):
        parts = [_extract_location(item) for item in value]
        return _clean_text("; ".join(part for part in parts if part))

    if not isinstance(value, dict):
        return _string_value(value)

    address = value.get("address")
    if isinstance(address, dict):
        parts = [
            _string_value(address.get("addressLocality")),
            _string_value(address.get("addressRegion")),
            _string_value(address.get("addressCountry")),
        ]
        return _clean_text(", ".join(part for part in parts if part))

    return _string_value(address) or _string_value(value.get("name"))


def _extract_from_meta(meta: dict[str, str]) -> JobMetadata:
    title = (
        meta.get("og:title")
        or meta.get("twitter:title")
        or meta.get("title")
    )
    company = (
        meta.get("company")
        or meta.get("job:company")
        or meta.get("application-name")
    )
    location = meta.get("job:location") or meta.get("location")

    if title and not company:
        title_parts = _split_title(title)
        title = title_parts.job_title or title
        company = title_parts.company

    return JobMetadata(
        job_title=_clean_text(title),
        company=_clean_text(company),
        location=_clean_text(location),
    )


def _extract_from_title(title: str | None) -> JobMetadata:
    if not title:
        return JobMetadata()
    return _split_title(title)


def _split_title(title: str) -> JobMetadata:
    normalized = _clean_text(title)
    if not normalized:
        return JobMetadata()

    for separator in (" at ", " | ", " - "):
        if separator in normalized:
            left, right = normalized.split(separator, 1)
            return JobMetadata(
                job_title=_clean_text(left),
                company=_clean_text(_strip_career_suffix(right)),
            )

    return JobMetadata(job_title=normalized)


def _strip_career_suffix(value: str) -> str:
    return re.sub(r"\b(careers|jobs|job board|application)\b.*$", "", value, flags=re.I)


def _string_value(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = unescape(re.sub(r"\s+", " ", value)).strip(" \t\r\n-|")
    return cleaned or None

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Any

from .base import AdapterContext, AdapterResult, SkeletonAdapter


class GreenhouseAdapter(SkeletonAdapter):
    provider = "greenhouse"
    adapter = "greenhouse_adapter"
    display_name = "Greenhouse"

    def plan(self, context: AdapterContext) -> AdapterResult:
        fields = _extract_application_fields(context.html)
        if not fields:
            return super().plan(context)

        return AdapterResult(
            provider=self.provider,
            adapter=self.adapter,
            status="planned",
            message=(
                "Greenhouse application field preflight completed; "
                "stop before any form execution."
            ),
            details={
                "field_count": len(fields),
                "fields": fields,
                "planned_steps": [
                    "inspect_application_fields",
                    "prepare_deterministic_fill",
                    "stop_before_final_submit",
                ],
                "review_reasons": ["final_submit_boundary"],
            },
        )


class _GreenhouseFieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.labels_by_target: dict[str, str] = {}
        self.raw_fields: list[dict[str, object]] = []
        self._label_target: str | None = None
        self._label_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value or "" for name, value in attrs}

        if tag == "label":
            self._label_target = attr_map.get("for") or None
            self._label_parts = []
            return

        if tag not in {"input", "select", "textarea"}:
            return

        field_type = attr_map.get("type") or tag
        if field_type.lower() in {"hidden", "submit", "button"}:
            return

        name = attr_map.get("name") or attr_map.get("id")
        field_id = attr_map.get("id") or name
        if not name and not field_id:
            return

        self.raw_fields.append(
            {
                "input_name": name,
                "input_id": field_id,
                "input_type": field_type,
                "required": (
                    "required" in attr_map
                    or attr_map.get("aria-required", "").lower() == "true"
                ),
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "label" or not self._label_target:
            return

        label = _clean_text(" ".join(self._label_parts))
        if label:
            self.labels_by_target[self._label_target] = label
        self._label_target = None
        self._label_parts = []

    def handle_data(self, data: str) -> None:
        if self._label_target:
            self._label_parts.append(data)


def _extract_application_fields(html: str | None) -> list[dict[str, object]]:
    if not html:
        return []

    parser = _GreenhouseFieldParser()
    parser.feed(html)

    fields: list[dict[str, object]] = []
    seen_keys: set[str] = set()
    for raw_field in parser.raw_fields:
        input_id = _string_value(raw_field.get("input_id"))
        input_name = _string_value(raw_field.get("input_name"))
        label = (
            parser.labels_by_target.get(input_id or "")
            or parser.labels_by_target.get(input_name or "")
            or _label_from_input_name(input_name)
        )
        field_key = _field_key(input_name, input_id, label)
        if not field_key or field_key in seen_keys:
            continue

        seen_keys.add(field_key)
        fields.append(
            {
                "field_key": field_key,
                "label": label,
                "input_name": input_name,
                "input_type": raw_field["input_type"],
                "required": raw_field["required"],
            }
        )

    return fields


def _field_key(*values: str | None) -> str | None:
    haystack = " ".join(value or "" for value in values).lower()
    if "first_name" in haystack or "first name" in haystack:
        return "first_name"
    if "last_name" in haystack or "last name" in haystack:
        return "last_name"
    if "email" in haystack:
        return "email"
    if "phone" in haystack:
        return "phone"
    if "resume" in haystack or "cv" in haystack:
        return "resume"
    if "cover_letter" in haystack or "cover letter" in haystack:
        return "cover_letter"
    return None


def _label_from_input_name(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"^job_application\[|\]$", "", value)
    cleaned = cleaned.replace("_", " ").strip()
    return cleaned.title() if cleaned else None


def _string_value(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = unescape(re.sub(r"\s+", " ", value)).strip()
    return cleaned or None

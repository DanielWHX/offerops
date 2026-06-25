from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any


TEXT_FIELDS = (
    "first_name",
    "last_name",
    "preferred_first_name",
    "email",
    "phone",
    "location_city",
)
TEXT_FIELD_LABELS = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "preferred_first_name": "Preferred First Name",
    "email": "Email",
    "phone": "Phone",
    "location_city": "Location (City)",
}
FILE_FIELDS = ("resume", "cover_letter")
CUSTOM_TEXT_FIELDS = {
    "linkedin_profile": "Please share your LinkedIn profile",
    "desired_salary": "What is your desired salary?",
    "current_gpa": "What is your current cumulative GPA?",
    "work_hours": "We are looking for someone to work 25 hours a week for 8-12 weeks. Knowing your school schedule, are you able to work that many hours?",
}
DROPDOWN_FIELDS = {
    "phone_country": "country",
    "visa_sponsorship": "question_67708023",
    "acknowledgement": "question_67708024",
    "gender": "gender",
    "hispanic_ethnicity": "hispanic_ethnicity",
    "race": "race",
    "veteran_status": "veteran_status",
    "disability_status": "disability_status",
}
EDUCATION_FIELDS = {
    "school": "school--0",
    "degree": "degree--0",
}
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> int:
    args = build_parser().parse_args()
    profile = load_profile(Path(args.profile_file))
    screenshot_path = Path(args.screenshot)
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "playwright is required for this demo runner; install it in the active "
            "environment with `python -m pip install playwright`."
        ) from exc

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=args.user_data_dir,
            executable_path=args.chrome_path,
            headless=args.headless,
            args=["--no-first-run", "--no-default-browser-check"],
        )
        page = context.new_page()
        page.set_default_timeout(args.timeout * 1000)
        exit_code = 1
        try:
            page.goto(args.url, wait_until="domcontentloaded")
            application_open_result = open_application_form(page)
            wait_for_greenhouse_form(page)
            guard_result = install_submit_guard(page)

            dropdown_result = fill_dropdown_fields(page, profile.get("dropdowns", {}))
            education_result = fill_education_fields(
                page, profile.get("education", {})
            )
            custom_text_result = fill_custom_text_fields(
                page, profile.get("custom_text", {})
            )
            file_result = fill_file_fields(page, profile["files"])
            text_result = fill_text_fields(page, profile["text"])
            page.screenshot(path=str(screenshot_path), full_page=True)

            result = {
                "url": args.url,
                "application_open": application_open_result,
                "text_fields": text_result,
                "custom_text_fields": custom_text_result,
                "dropdown_fields": dropdown_result,
                "education_fields": education_result,
                "file_fields": file_result,
                "submit_guard": guard_result,
                "screenshot": str(screenshot_path),
                "safety": {
                    "browser_control": "playwright_chrome",
                    "final_submit": "blocked_not_clicked",
                    "profile_values": "not_printed",
                },
            }
            print(json.dumps(result, indent=2, sort_keys=True), flush=True)
            exit_code = 0
        except Exception as exc:
            error_screenshot_path = screenshot_path.with_name(
                f"{screenshot_path.stem}_error{screenshot_path.suffix}"
            )
            safe_screenshot(page, error_screenshot_path)
            print(
                json.dumps(
                    {
                        "url": args.url,
                        "status": "failed",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "screenshot": str(error_screenshot_path),
                        "safety": {
                            "browser_control": "playwright_chrome",
                            "final_submit": "blocked_not_clicked",
                            "profile_values": "not_printed",
                        },
                    },
                    indent=2,
                    sort_keys=True,
                ),
                flush=True,
            )
            exit_code = 1
        finally:
            if args.keep_open_seconds:
                time.sleep(args.keep_open_seconds)
            context.close()
        return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fill a Greenhouse application page through Playwright and stop before submit."
    )
    parser.add_argument("url", help="Greenhouse job application URL")
    parser.add_argument(
        "--profile-file",
        default="tests/fixtures/browser_applicant_profile.json",
        help="Fake applicant profile JSON used for the demo",
    )
    parser.add_argument(
        "--cdp-url",
        default="",
        help="Deprecated compatibility option; Playwright does not use this value.",
    )
    parser.add_argument("--chrome-path", default=DEFAULT_CHROME)
    parser.add_argument(
        "--user-data-dir",
        default="/tmp/offerops-greenhouse-playwright",
        help="Dedicated Chrome profile directory",
    )
    parser.add_argument(
        "--screenshot",
        default="artifacts/greenhouse_fill_demo.png",
        help="Screenshot output path",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--keep-open-seconds", type=float, default=0.0)
    parser.add_argument("--close-chrome", action="store_true")
    parser.add_argument("--headless", action="store_true")
    return parser


def load_profile(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("profile file must contain a JSON object")

    if isinstance(payload.get("identity"), dict):
        return load_nested_profile(payload, path)

    return load_flat_profile(payload, path)


def load_flat_profile(payload: dict[str, Any], path: Path) -> dict[str, dict[str, str]]:
    text_profile: dict[str, str] = {}
    file_profile: dict[str, str] = {}
    for key in TEXT_FIELDS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            text_profile[key] = value

    for key in FILE_FIELDS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            file_profile[key] = str((path.parent / value).resolve())

    return {
        "text": text_profile,
        "files": file_profile,
        "custom_text": {},
        "dropdowns": {},
        "education": {},
    }


def load_nested_profile(payload: dict[str, Any], path: Path) -> dict[str, dict[str, str]]:
    identity = dict_value(payload, "identity")
    account = dict_value(payload, "account")
    resume = dict_value(payload, "resume")
    work_authorization = dict_value(payload, "work_authorization")
    default_answers = dict_value(payload, "default_answers")
    application_answers = dict_value(payload, "application_answers")
    app_compensation = dict_value(application_answers, "compensation")
    app_availability = dict_value(application_answers, "availability")
    app_certification = dict_value(application_answers, "certification")
    app_self_id = dict_value(application_answers, "self_identification")
    education = dict_value(payload, "education")

    first_name = string_value(identity, "first_name")
    text_profile = compact_strings(
        {
            "first_name": first_name,
            "last_name": string_value(identity, "last_name"),
            "preferred_first_name": first_name,
            "email": string_value(identity, "email") or string_value(account, "email"),
            "phone": string_value(identity, "phone"),
            "location_city": string_value(application_answers, "current_location")
            or string_value(identity, "location"),
        }
    )
    file_profile = compact_strings(
        {
            "resume": string_value(resume, "resume_path")
            or string_value(resume, "original_resume_path"),
            "cover_letter": string_value(payload, "cover_letter"),
        }
    )
    custom_text = compact_strings(
        {
            "linkedin_profile": string_value(identity, "linkedin")
            or string_value(default_answers, "linkedin"),
            "desired_salary": string_value(app_compensation, "default_answer")
            or string_value(default_answers, "compensation"),
            "current_gpa": string_value(payload, "gpa")
            or os.environ.get("OFFEROPS_GPA", "").strip(),
            "work_hours": string_value(app_availability, "work_hours")
            or string_value(app_availability, "able_to_work_hours")
            or string_value(app_availability, "able_to_relocate_schedule"),
        }
    )
    dropdowns = compact_strings(
        {
            "phone_country": infer_phone_country(text_profile.get("phone", "")),
            "visa_sponsorship": yes_no_from_text(
                string_value(work_authorization, "future_sponsorship_required")
            ),
            "acknowledgement": "Yes" if app_certification else "",
            "gender": normalize_self_identification_answer(
                string_value(default_answers, "gender"), "gender"
            ),
            "hispanic_ethnicity": string_value(app_self_id, "hispanic_latino")
            or string_value(default_answers, "hispanic_latino"),
            "race": string_value(default_answers, "race"),
            "veteran_status": string_value(default_answers, "veteran_status"),
            "disability_status": normalize_self_identification_answer(
                string_value(default_answers, "disability_status"),
                "disability_status",
            ),
        }
    )
    education_profile = compact_strings(
        {
            "school": string_value(education, "current_school"),
            "degree": string_value(education, "current_degree"),
        }
    )

    return {
        "text": text_profile,
        "files": file_profile,
        "custom_text": custom_text,
        "dropdowns": dropdowns,
        "education": education_profile,
    }


def dict_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def string_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def compact_strings(payload: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in payload.items() if value}


def infer_phone_country(phone: str) -> str:
    digits = digits_only(phone)
    if phone.strip().startswith("+1") or len(digits) == 10:
        return "United States"
    return ""


def yes_no_from_text(value: str) -> str:
    lowered = value.strip().lower()
    if lowered.startswith("yes"):
        return "Yes"
    if lowered.startswith("no"):
        return "No"
    return ""


def normalize_self_identification_answer(value: str, field_key: str) -> str:
    lowered = value.lower().replace("’", "'")
    if "don't wish" not in lowered and "do not wish" not in lowered:
        return value
    if field_key == "gender":
        return "Decline To Self Identify"
    if field_key == "disability_status":
        return "I do not want to answer"
    return value


def open_application_form(page: Any) -> dict[str, Any]:
    if greenhouse_form_visible(page):
        return {"status": "already_open", "clicked_count": 0, "clicked": []}

    apply_button = page.get_by_role("link", name="Apply").or_(
        page.get_by_role("button", name="Apply")
    )
    apply_button.first.click()
    wait_for_greenhouse_form(page)
    return {"status": "clicked_apply", "clicked_count": 1, "clicked": ["Apply"]}


def greenhouse_form_visible(page: Any) -> bool:
    return bool(
        page.locator("body").evaluate(
            """body => {
              const text = body.innerText || '';
              return text.includes('First Name') &&
                text.includes('Email') &&
                text.includes('Resume/CV');
            }"""
        )
    )


def wait_for_greenhouse_form(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const text = document.body && document.body.innerText || '';
          return text.includes('First Name') &&
            text.includes('Email') &&
            text.includes('Resume/CV');
        }"""
    )


def fill_text_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for field_key in TEXT_FIELDS:
        value = profile.get(field_key)
        if not value:
            results.append(
                {
                    "field_key": field_key,
                    "status": "missing_profile_value",
                    "value_present": False,
                }
            )
            continue

        status = (
            fill_location(page, value)
            if field_key == "location_city"
            else fill_labeled_input(page, TEXT_FIELD_LABELS[field_key], value)
        )
        results.append(
            {
                "field_key": field_key,
                "status": status,
                "value_present": True,
                "verified_value_matches": field_value_matches(
                    page, field_key, TEXT_FIELD_LABELS[field_key], value
                ),
            }
        )

    return results


def fill_labeled_input(page: Any, label: str, value: str) -> str:
    locator = page.locator(f'input[aria-label="{label}"], textarea[aria-label="{label}"]')
    if locator.count() == 0:
        locator = element_by_visible_label(page, label, "input, textarea")
    target = first_visible(locator)
    if target is None:
        return "not_found"

    target.fill(value)
    target.dispatch_event("input")
    target.dispatch_event("change")
    target.evaluate("element => element.blur()")
    return "filled"


def first_visible(locator: Any) -> Any | None:
    for index in range(locator.count()):
        candidate = locator.nth(index)
        if candidate.is_visible():
            return candidate
    return None


def fill_custom_text_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for field_key, label in CUSTOM_TEXT_FIELDS.items():
        value = profile.get(field_key)
        if not value:
            results.append(
                {
                    "field_key": field_key,
                    "status": "missing_profile_value",
                    "value_present": False,
                }
            )
            continue

        status = fill_labeled_input(page, label, value)
        results.append(
            {
                "field_key": field_key,
                "status": status,
                "value_present": True,
                "verified_value_matches": field_value_matches(
                    page, field_key, label, value
                ),
            }
        )
    return results


def fill_dropdown_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for field_key, field_id in DROPDOWN_FIELDS.items():
        value = profile.get(field_key)
        if not value:
            results.append(
                {
                    "field_key": field_key,
                    "status": "missing_profile_value",
                    "value_present": False,
                }
            )
            continue

        status = select_react_combobox(page, field_id, value)
        results.append(
            {
                "field_key": field_key,
                "status": status,
                "value_present": True,
                "verified_value_matches": react_combobox_value_matches(
                    page, field_id, value
                ),
            }
        )
    return results


def fill_education_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for field_key, field_id in EDUCATION_FIELDS.items():
        if not element_id_is_visible(page, field_id):
            results.append(
                {
                    "field_key": field_key,
                    "status": "not_present",
                    "value_present": False,
                }
            )
            continue

        value = profile.get(field_key)
        if not value:
            results.append(
                {
                    "field_key": field_key,
                    "status": "missing_profile_value",
                    "value_present": False,
                }
            )
            continue

        status = select_education_combobox(page, field_id, field_key, value)
        results.append(
            {
                "field_key": field_key,
                "status": status,
                "value_present": True,
                "verified_value_matches": education_value_matches(
                    page, field_id, field_key, value
                ),
            }
        )
    return results


def element_id_is_visible(page: Any, field_id: str) -> bool:
    locator = page.locator(f"#{field_id}")
    return locator.count() > 0 and locator.first.is_visible()


def select_education_combobox(
    page: Any, field_id: str, field_key: str, value: str
) -> str:
    input_locator = page.locator(f"#{field_id}")
    if input_locator.count() == 0:
        return "not_present"

    for term in education_search_terms(field_key, value):
        input_locator.first.scroll_into_view_if_needed()
        input_locator.first.click(force=True)
        input_locator.first.fill(term)
        page.wait_for_timeout(2500 if field_key == "school" else 1000)
        if not click_visible_option_matching(
            page, term
        ) and not click_first_visible_option(page):
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(200)
            page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        if education_value_matches(page, field_id, field_key, value):
            return "filled"

    return "needs_review"


def education_search_terms(field_key: str, value: str) -> list[str]:
    if field_key == "school":
        return school_search_terms(value)
    if field_key == "degree":
        lowered = value.lower()
        if "master" in lowered:
            return ["Master", value]
        if "bachelor" in lowered:
            return ["Bachelor", value]
    return [value]


def school_search_terms(value: str) -> list[str]:
    terms = [value]
    normalized = value.replace("-", " ")
    if normalized != value:
        terms.append(normalized)

    lowered = normalized.lower()
    if (
        "university of illinois" in lowered
        and "urbana" in lowered
        and "champaign" in lowered
    ):
        terms.extend(
            [
                "University of Illinois at Urbana-Champaign",
                "University of Illinois at Urbana Champaign",
                "Illinois Urbana",
            ]
        )
    return unique_strings(terms)


def education_value_matches(
    page: Any, field_id: str, field_key: str, expected: str
) -> bool:
    tokens = education_match_tokens(field_key, expected)
    if not tokens:
        return False
    return bool(
        page.locator("body").evaluate(
            """(body, args) => {
              const {fieldId, tokens} = args;
              const input = document.getElementById(fieldId);
              if (!input) return false;
              const field = input.closest('.field-wrapper') ||
                input.closest('.select__container') ||
                input.closest('.select-shell');
              const text = ((field && (field.innerText || field.textContent)) || '')
                .replace(/\\s+/g, ' ')
                .trim()
                .toLowerCase();
              return tokens.some(token => text.includes(token));
            }""",
            {"fieldId": field_id, "tokens": tokens},
        )
    )


def education_match_tokens(field_key: str, value: str) -> list[str]:
    lowered = value.lower().strip()
    if not lowered:
        return []
    if field_key == "school":
        tokens: list[str] = []
        for term in school_search_terms(value):
            tokens.extend(normalized_tokens(term))
        return unique_strings(tokens)
    if field_key == "degree":
        if "master" in lowered:
            return ["master"]
        if "bachelor" in lowered:
            return ["bachelor"]
    return normalized_tokens(value)


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def fill_location(page: Any, value: str) -> str:
    if select_location_autocomplete(page, value):
        return "filled"
    return "needs_review"


def select_location_autocomplete(page: Any, value: str) -> bool:
    input_locator = page.locator("#candidate-location")
    if input_locator.count() == 0:
        return False

    for term in location_search_terms(value):
        input_locator.first.scroll_into_view_if_needed()
        input_locator.first.click(force=True)
        input_locator.first.fill(term)
        page.wait_for_timeout(1500)
        if click_first_visible_option(page):
            page.wait_for_timeout(500)
            page.keyboard.press("Tab")
            page.wait_for_timeout(300)
            if location_field_is_valid(page, value):
                return True

    return False


def location_search_terms(value: str) -> list[str]:
    terms = [value]
    city = value.split(",", 1)[0].strip()
    if city and city not in terms:
        terms.insert(0, city)
    return terms


def click_first_visible_option(page: Any) -> bool:
    return bool(
        page.locator("body").evaluate(
            """() => {
              const visible = element => {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                return rect.width > 0 && rect.height > 0 &&
                  style.visibility !== 'hidden' && style.display !== 'none';
              };
              const option = Array.from(document.querySelectorAll('[role="option"], .select__option'))
                .filter(visible)[0];
              if (!option) return false;
              option.click();
              return true;
            }"""
        )
    )


def location_field_is_valid(page: Any, expected: str) -> bool:
    city = expected.split(",", 1)[0].strip().lower()
    if not city:
        return False
    return bool(
        page.locator("body").evaluate(
            """(body, city) => {
              const input = document.getElementById('candidate-location');
              if (!input) return false;
              const field = input.closest('.field-wrapper');
              const text = ((field && (field.innerText || field.textContent)) || '')
                .replace(/\\s+/g, ' ')
                .trim()
                .toLowerCase();
              const error = document.getElementById('candidate-location-error');
              const errorVisible = error && error.offsetParent !== null &&
                /please enter your location/i.test(error.innerText || error.textContent || '');
              return text.includes(city) && !errorVisible;
            }""",
            city,
        )
    )


def select_react_combobox(page: Any, field_id: str, value: str) -> str:
    input_locator = page.locator(f"#{field_id}")
    if input_locator.count() == 0:
        return "not_found"

    input_locator.first.scroll_into_view_if_needed()
    input_locator.first.click(force=True)
    input_locator.first.fill(value)
    page.wait_for_timeout(800)

    if not click_visible_option_matching(page, value):
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    return "filled" if react_combobox_value_matches(page, field_id, value) else "needs_review"


def click_visible_option_matching(page: Any, expected: str) -> bool:
    return bool(
        page.locator("body").evaluate(
            """(body, expectedTokens) => {
              const visible = element => {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                return rect.width > 0 && rect.height > 0 &&
                  style.visibility !== 'hidden' && style.display !== 'none';
              };
              const normalize = text => (text || '')
                .replace(/\\s+/g, ' ')
                .trim()
                .toLowerCase();
              const options = Array.from(document.querySelectorAll('[role="option"], .select__option'))
                .filter(visible);
              for (const token of expectedTokens) {
                const match = options.find(option => normalize(option.innerText || option.textContent).includes(token));
                if (match) {
                  match.click();
                  return true;
                }
              }
              return false;
            }""",
            normalized_tokens(expected),
        )
    )


def react_combobox_value_matches(page: Any, field_id: str, expected: str) -> bool:
    expected_tokens = normalized_tokens(expected)
    if field_id == "country" and expected.lower() == "united states":
        expected_tokens.append("+1")
    if not expected_tokens:
        return False
    return bool(
        page.locator("body").evaluate(
            """(body, args) => {
              const {fieldId, expectedTokens} = args;
              const input = document.getElementById(fieldId);
              if (!input) return false;
              const control = input.closest('.select__control') ||
                input.closest('.select__container');
              const field = input.closest('.field-wrapper');
              const selected = control && control.querySelector('.select__single-value');
              const values = [
                selected && (selected.innerText || selected.textContent),
                field && (field.innerText || field.textContent),
              ].map(value => (value || '').replace(/\\s+/g, ' ').trim().toLowerCase());
              return expectedTokens.some(token => values.some(value => value.includes(token)));
            }""",
            {"fieldId": field_id, "expectedTokens": expected_tokens},
        )
    )


def normalized_tokens(value: str) -> list[str]:
    text = value.lower().replace("’", "'").strip()
    tokens = [text]
    if "," in text:
        tokens.append(text.split(",", 1)[0].strip())
    if "don't wish to answer" in text:
        tokens.extend(
            [
                "decline",
                "do not wish",
                "don't wish",
                "i don't wish",
                "i do not wish",
            ]
        )
    if text in {"yes", "no"}:
        tokens.append(text)
    return [token for token in tokens if token]


def element_by_visible_label(page: Any, label: str, selector: str) -> Any:
    return page.locator(
        f"""
        xpath=//*[self::label or self::div or self::span or self::p]
          [normalize-space(translate(substring-before(concat(., '\n'), '\n'), '*', '')) = "{label}"]
          /ancestor-or-self::*[position() <= 1]
        """
    ).locator(selector)


def field_value_matches(page: Any, field_key: str, label: str, expected: str) -> bool:
    if field_key == "location_city":
        return location_field_is_valid(page, expected)

    locator = page.locator(f'input[aria-label="{label}"], textarea[aria-label="{label}"]')
    if locator.count() == 0:
        locator = element_by_visible_label(page, label, "input, textarea")
    target = first_visible(locator)
    if target is None:
        return False
    if field_key == "phone":
        return digits_only(target.input_value()).endswith(digits_only(expected))
    return target.input_value() == expected


def digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def fill_file_fields(page: Any, files: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    resume_path = files.get("resume")
    if resume_path:
        results.append(upload_file_input(page, "resume", 0, resume_path))
    else:
        results.append({"field_key": "resume", "status": "missing_file"})

    cover_letter_path = files.get("cover_letter")
    if cover_letter_path:
        results.append(fill_cover_letter_manually(page, cover_letter_path))
    else:
        results.append({"field_key": "cover_letter", "status": "missing_file"})

    return results


def upload_file_input(page: Any, field_key: str, index: int, file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"field_key": field_key, "status": "missing_file"}

    attached = upload_file_with_visible_button(page, field_key, path)
    if not attached:
        inputs = page.locator('input[type="file"]')
        if inputs.count() <= index:
            return {"field_key": field_key, "status": "not_found"}
        inputs.nth(index).set_input_files(str(path))

    try:
        page.get_by_text(path.name).wait_for(timeout=12_000)
        file_visible = True
    except Exception:
        file_visible = False

    return {
        "field_key": field_key,
        "status": "attached" if file_visible else "upload_pending",
        "file_present": True,
        "verified_file_visible": file_visible,
    }


def upload_file_with_visible_button(page: Any, field_key: str, path: Path) -> bool:
    label = "Resume/CV" if field_key == "resume" else "Cover Letter"
    try:
        with page.expect_file_chooser(timeout=5_000) as file_chooser_info:
            if not click_upload_option(page, label, "Attach"):
                return False
        file_chooser_info.value.set_files(str(path))
        return True
    except Exception:
        return False


def fill_cover_letter_manually(page: Any, file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"field_key": "cover_letter", "status": "missing_file"}

    if not click_upload_option(page, "Cover Letter", "Enter manually"):
        return {"field_key": "cover_letter", "status": "manual_option_not_found"}

    textarea = cover_letter_textarea(page)
    if textarea.count() == 0:
        return {"field_key": "cover_letter", "status": "manual_textarea_not_found"}

    text = path.read_text(encoding="utf-8")
    textarea.first.fill(text)
    return {
        "field_key": "cover_letter",
        "status": "filled_manually",
        "file_present": True,
        "verified_value_matches": textarea.first.input_value() == text,
    }


def click_upload_option(page: Any, label: str, option: str) -> bool:
    return bool(
        page.locator("body").evaluate(
            """(body, args) => {
              const {label, option} = args;
              const normalize = text => (text || '')
                .replace(/\\*/g, '')
                .replace(/\\s+/g, ' ')
                .trim()
                .toLowerCase();
              const visible = element => {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                return rect.width > 0 && rect.height > 0 &&
                  style.visibility !== 'hidden' && style.display !== 'none';
              };
              const wantedLabel = normalize(label);
              const wantedOption = normalize(option);
              const labels = Array.from(document.querySelectorAll('label, div, span, p'))
                .filter(visible);
              for (const element of labels) {
                const firstLine = normalize((element.innerText || element.textContent || '').split('\\n')[0]);
                if (firstLine !== wantedLabel) continue;
                let root = element;
                for (let depth = 0; root && depth < 8; depth += 1, root = root.parentElement) {
                  const button = Array.from(root.querySelectorAll('button, [role="button"], a, div, span'))
                    .filter(visible)
                    .find(candidate => normalize(candidate.innerText || candidate.textContent) === wantedOption);
                  if (button) {
                    button.click();
                    return true;
                  }
                }
              }
              return false;
            }""",
            {"label": label, "option": option},
        )
    )


def cover_letter_textarea(page: Any) -> Any:
    return page.locator("body").locator(
        """xpath=//*[self::label or self::div or self::span or self::p]
          [normalize-space(translate(substring-before(concat(., '\n'), '\n'), '*', '')) = "Cover Letter"]
          /ancestor::*[contains(@class, "field-wrapper") or contains(@class, "file-upload")][1]
          //textarea"""
    )


def install_submit_guard(page: Any) -> dict[str, Any]:
    return page.locator("body").evaluate(
        """() => {
          const controls = Array.from(
            document.querySelectorAll('button, input[type="submit"], input[type="button"]')
          ).filter(element => {
            const text = (element.innerText || element.value || '').toLowerCase();
            return /submit|apply/.test(text);
          });
          for (const element of controls) {
            if (element.dataset.offeropsSubmitGuard === 'true') continue;
            element.dataset.offeropsSubmitGuard = 'true';
            element.addEventListener('click', event => {
              event.preventDefault();
              event.stopImmediatePropagation();
              return false;
            }, true);
          }
          return {controls_guarded: controls.length, final_submit: 'blocked_not_clicked'};
        }"""
    )


def safe_screenshot(page: Any, path: Path) -> None:
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        return


if __name__ == "__main__":
    raise SystemExit(main())

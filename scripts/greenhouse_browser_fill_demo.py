from __future__ import annotations

import argparse
import json
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

            text_result = fill_text_fields(page, profile["text"])
            file_result = fill_file_fields(page, profile["files"])
            guard_result = install_submit_guard(page)
            page.screenshot(path=str(screenshot_path), full_page=True)

            result = {
                "url": args.url,
                "application_open": application_open_result,
                "text_fields": text_result,
                "file_fields": file_result,
                "submit_guard": guard_result,
                "screenshot": str(screenshot_path),
                "safety": {
                    "browser_control": "playwright_chrome",
                    "final_submit": "blocked_not_clicked",
                    "profile_values": "not_printed",
                },
            }
            print(json.dumps(result, indent=2, sort_keys=True))
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
                )
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

    return {"text": text_profile, "files": file_profile}


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
    if locator.count() == 0:
        return "not_found"

    locator.first.fill(value)
    return "filled"


def fill_location(page: Any, value: str) -> str:
    focused = page.locator("body").evaluate(
        """(body) => {
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
          const direct = document.querySelector('#candidate-location');
          if (direct && visible(direct)) {
            direct.scrollIntoView({block: 'center'});
            direct.focus();
            return true;
          }
          const labels = Array.from(document.querySelectorAll('label, div, span, p'))
            .filter(visible);
          for (const label of labels) {
            const firstLine = normalize((label.innerText || label.textContent || '').split('\\n')[0]);
            if (firstLine !== 'location (city)') continue;
            const field = label.closest('.field-wrapper') || label.parentElement;
            const combo = field && Array.from(field.querySelectorAll('input[role="combobox"]')).filter(visible)[0];
            if (combo) {
              combo.scrollIntoView({block: 'center'});
              combo.focus();
              return true;
            }
          }
          return false;
        }"""
    )
    if not focused:
        return "not_found"

    page.keyboard.press("Meta+A")
    page.keyboard.insert_text(value)
    page.wait_for_timeout(1000)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    if field_value_matches(page, "location_city", TEXT_FIELD_LABELS["location_city"], value):
        return "filled"
    return "needs_review"


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
        return bool(
            page.locator("body").evaluate(
                """(body, expected) => {
                  const input = document.querySelector('#candidate-location');
                  if (!input) return false;
                  const field = input.closest('.field-wrapper');
                  const control = input.closest('.select__control');
                  const values = [
                    input.value || '',
                    field && (field.innerText || field.textContent || ''),
                    control && (control.innerText || control.textContent || ''),
                  ];
                  return values.some(value => value.includes(expected));
                }""",
                expected,
            )
        )

    locator = page.locator(f'input[aria-label="{label}"], textarea[aria-label="{label}"]')
    if locator.count() == 0:
        locator = element_by_visible_label(page, label, "input, textarea")
    if locator.count() == 0:
        return False
    return locator.first.input_value() == expected


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

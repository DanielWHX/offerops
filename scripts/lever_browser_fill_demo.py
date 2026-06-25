from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TEXT_FIELD_SELECTORS = {
    "full_name": 'input[name="name"]',
    "email": 'input[name="email"]',
    "phone": 'input[name="phone"]',
    "location_city": 'input[name="location"]',
}
LINK_FIELD_SELECTORS = {
    "linkedin_profile": 'input[name="urls[LinkedIn]"]',
}
FILLED_STATUSES = {"filled", "attached"}
MISSING_PROFILE_STATUSES = {"missing_profile_value", "missing_file"}


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
            wait_for_lever_form(page)
            guard_result = install_submit_guard(page)

            text_result = fill_text_fields(page, profile["text"])
            link_result = fill_link_fields(page, profile.get("custom_text", {}))
            file_result = fill_file_fields(page, profile["files"])
            final_report = build_final_report(
                [text_result, link_result, file_result], guard_result
            )
            page.screenshot(path=str(screenshot_path), full_page=True)

            result = {
                "url": args.url,
                "final_report": final_report,
                "text_fields": text_result,
                "link_fields": link_result,
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
        description="Fill a Lever application page through Playwright and stop before submit."
    )
    parser.add_argument("url", help="Lever job application URL")
    parser.add_argument(
        "--profile-file",
        default="tests/fixtures/browser_applicant_profile.json",
        help="Applicant profile JSON used for the demo",
    )
    parser.add_argument("--chrome-path", default=DEFAULT_CHROME)
    parser.add_argument(
        "--user-data-dir",
        default="/tmp/offerops-lever-playwright",
        help="Dedicated Chrome profile directory",
    )
    parser.add_argument(
        "--screenshot",
        default="artifacts/lever_fill_demo.png",
        help="Screenshot output path",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--keep-open-seconds", type=float, default=0.0)
    parser.add_argument("--headless", action="store_true")
    return parser


def load_profile(path: Path) -> dict[str, dict[str, str]]:
    return _greenhouse_helpers().load_profile(path)


def _greenhouse_helpers() -> Any:
    script_path = Path(__file__).with_name("greenhouse_browser_fill_demo.py")
    module_name = "_offerops_greenhouse_browser_fill_demo"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load greenhouse browser helper module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def wait_for_lever_form(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const text = document.body && document.body.innerText || '';
          return text.includes('Full name') &&
            text.includes('Email') &&
            text.includes('Phone') &&
            document.querySelector('input[name="resume"]');
        }"""
    )


def fill_text_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    full_name = " ".join(
        value
        for value in (profile.get("first_name", ""), profile.get("last_name", ""))
        if value
    ).strip()
    values = {
        "full_name": full_name,
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "location_city": profile.get("location_city", ""),
    }
    return [
        fill_input(page, field_key, selector, values.get(field_key, ""))
        for field_key, selector in TEXT_FIELD_SELECTORS.items()
    ]


def fill_link_fields(page: Any, profile: dict[str, str]) -> list[dict[str, Any]]:
    return [
        fill_input(page, field_key, selector, profile.get(field_key, ""))
        for field_key, selector in LINK_FIELD_SELECTORS.items()
    ]


def fill_input(page: Any, field_key: str, selector: str, value: str) -> dict[str, Any]:
    if not value:
        return {
            "field_key": field_key,
            "status": "missing_profile_value",
            "value_present": False,
        }
    locator = page.locator(selector)
    if locator.count() == 0 or not locator.first.is_visible():
        return {"field_key": field_key, "status": "not_found", "value_present": True}
    locator.first.fill(value)
    locator.first.dispatch_event("input")
    locator.first.dispatch_event("change")
    locator.first.evaluate("element => element.blur()")
    verified = locator.first.input_value() == value
    return {
        "field_key": field_key,
        "status": "filled" if verified else "needs_review",
        "value_present": True,
        "verified_value_matches": verified,
    }


def fill_file_fields(page: Any, files: dict[str, str]) -> list[dict[str, Any]]:
    resume_path = files.get("resume")
    if not resume_path:
        return [{"field_key": "resume", "status": "missing_file"}]

    path = Path(resume_path)
    if not path.exists():
        return [{"field_key": "resume", "status": "missing_file"}]

    file_input = page.locator('input[name="resume"]')
    if file_input.count() == 0:
        return [{"field_key": "resume", "status": "not_found"}]

    file_input.first.set_input_files(str(path))
    page.wait_for_timeout(1500)
    visible = file_visible(page, path.name)
    return [
        {
            "field_key": "resume",
            "status": "attached" if visible else "needs_review",
            "file_present": True,
            "verified_file_visible": visible,
        }
    ]


def file_visible(page: Any, filename: str) -> bool:
    return bool(
        page.locator("body").evaluate(
            """(body, filename) =>
              (body.innerText || '').toLowerCase().includes(filename.toLowerCase())""",
            filename,
        )
    )


def build_final_report(
    field_groups: list[list[dict[str, Any]]], submit_guard: dict[str, Any]
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "filled": [],
        "missing_profile": [],
        "needs_review": [],
        "final_submit_blocked": submit_guard.get("final_submit")
        == "blocked_not_clicked",
    }
    for field_group in field_groups:
        for field in field_group:
            field_key = str(field.get("field_key", "")).strip()
            if not field_key:
                continue
            status = field.get("status")
            if status in MISSING_PROFILE_STATUSES:
                report["missing_profile"].append(field_key)
            elif status in FILLED_STATUSES and field_is_verified(field):
                report["filled"].append(field_key)
            else:
                report["needs_review"].append(field_key)
    return report


def field_is_verified(field: dict[str, Any]) -> bool:
    for key in ("verified_value_matches", "verified_file_visible"):
        if key in field and field[key] is False:
            return False
    return True


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

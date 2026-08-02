#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "playwright>=1.56.0",
#   "typer>=0.16.1",
# ]
# ///
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)

EXTRACT_SCRIPT = r"""
Array.from(document.querySelectorAll("table tr")).map(d => {
  const cells = d.querySelectorAll("td, th");
  const [model, score] = [(cells[2].querySelector("a")?.innerText ?? cells[2].innerText).split(/\n/)[0], cells[3].innerText.split(/\s/)[0]];
  return `${model}\t${score}`;
}).join("\n");
""".strip()


def describe() -> None:
    """Print the machine-readable command contract."""

    typer.echo(
        json.dumps(
            {
                "description": "Download an LMArena leaderboard TSV with Playwright.",
                "arguments": {
                    "url": "Leaderboard URL to visit.",
                    "output": "Path to write the TSV export.",
                },
                "options": {
                    "--browser": "Browser mode: auto, cdp, or launch. Default: auto.",
                    "--cdp": "CDP endpoint used by cdp/auto mode. Default: http://localhost:9222",
                    "--executable": "Optional Chrome/Chromium executable for launch mode.",
                    "--timeout": "Navigation and table wait timeout in milliseconds.",
                    "--format": "Use json for structured output or text for a plain summary.",
                    "--describe": "Print this schema and exit.",
                },
                "output": {
                    "url": "Visited URL.",
                    "path": "Written TSV path.",
                    "lines": "Number of non-empty output lines.",
                    "bytes": "Number of bytes written.",
                },
            },
            indent=2,
        )
    )


def default_executable() -> str | None:
    """Find a locally installed Chrome/Chromium executable."""

    configured = os.environ.get("LLMPRICING_CHROMIUM")
    candidates = [configured] if configured else []
    candidates.extend(
        [
            shutil.which("chrome"),
            shutil.which("chromium"),
            os.path.expandvars(r"%LOCALAPPDATA%\Chromium\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        ]
    )
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def write_leaderboard(
    *,
    url: str,
    output: Path,
    cdp: str,
    browser_mode: str,
    executable: str | None,
    timeout: int,
) -> dict[str, str | int]:
    """Visit a leaderboard page and save the extracted leaderboard."""

    browser = None
    owns_browser = False
    with sync_playwright() as p:
        if browser_mode in {"auto", "cdp"}:
            try:
                browser = p.chromium.connect_over_cdp(cdp, timeout=timeout)
            except PlaywrightError:
                if browser_mode == "cdp":
                    raise
        if browser is None:
            launch_args = {"headless": True}
            if executable:
                launch_args["executable_path"] = executable
            browser = p.chromium.launch(**launch_args)
            owns_browser = True
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        try:
            typer.echo(f"Opening {url}", err=True)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            page.wait_for_function(
                "() => [...document.querySelectorAll('table tr')].some(row => row.querySelectorAll('td, th').length >= 4)",
                timeout=timeout,
            )
            value = page.evaluate(EXTRACT_SCRIPT)
        finally:
            page.close()
            if owns_browser:
                browser.close()

    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("The leaderboard extraction returned no text.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value.rstrip() + "\n", encoding="utf-8")
    return {
        "url": url,
        "path": str(output),
        "lines": len([line for line in value.splitlines() if line.strip()]),
        "bytes": output.stat().st_size,
    }


@app.command()
def main(
    url: Annotated[str | None, typer.Argument(help="Leaderboard URL to visit.")] = None,
    output: Annotated[
        Path | None,
        typer.Argument(help="Path where the TSV export should be written."),
    ] = None,
    cdp: Annotated[str, typer.Option("--cdp", help="CDP endpoint.")] = "http://localhost:9222",
    browser_mode: Annotated[
        str,
        typer.Option("--browser", help="Browser mode: auto, cdp, or launch."),
    ] = "auto",
    executable: Annotated[
        str | None,
        typer.Option("--executable", help="Chrome/Chromium executable for launch mode."),
    ] = None,
    timeout: Annotated[
        int,
        typer.Option("--timeout", min=1000, help="Timeout in milliseconds."),
    ] = 60_000,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: json or text."),
    ] = "json",
    show_description: Annotated[
        bool,
        typer.Option("--describe", help="Print the command schema and exit."),
    ] = False,
) -> None:
    """Download a leaderboard page to the TSV shape expected by update_elo.py."""

    if show_description:
        describe()
        return
    if url is None or output is None:
        typer.echo("Error: URL and output path are required unless --describe is used.", err=True)
        raise typer.Exit(code=2)
    if output_format not in {"json", "text"}:
        typer.echo("Error: --format must be json or text.", err=True)
        raise typer.Exit(code=2)
    if browser_mode not in {"auto", "cdp", "launch"}:
        typer.echo("Error: --browser must be auto, cdp, or launch.", err=True)
        raise typer.Exit(code=2)
    if executable and not Path(executable).is_file():
        typer.echo(f"Error: executable does not exist: {executable}", err=True)
        raise typer.Exit(code=2)
    if executable is None:
        executable = default_executable()

    try:
        summary = write_leaderboard(
            url=url,
            output=output,
            cdp=cdp,
            browser_mode=browser_mode,
            executable=executable,
            timeout=timeout,
        )
    except (PlaywrightTimeoutError, PlaywrightError) as exc:
        typer.echo(f"Error: timed out while loading {url}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if output_format == "json" or not sys.stdout.isatty():
        typer.echo(json.dumps(summary, indent=2))
    else:
        typer.echo(f"Wrote {summary['lines']} lines to {summary['path']}")


if __name__ == "__main__":
    app()

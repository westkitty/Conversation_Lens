#!/usr/bin/env python3
"""Measure generated virtual-microphone-to-visible-cue latency in Brave.

Uses the real local Conversation Lens HTTP server and installed local speech
models. Chromium's virtual microphone replays generated speech; this is not a
physical-microphone or human-speech acceptance test. The report omits transcript
text and audio and is written only to stdout.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
APP = ROOT / "Conversation_Lens_Intelligent_Speaker_v6"
SERVER = APP / "server.py"
BRAVE = Path(os.environ.get(
    "LENS_BROWSER_EXECUTABLE",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"))
SAY = Path("/usr/bin/say")
FFMPEG = Path("/opt/homebrew/bin/ffmpeg")
if not FFMPEG.exists():
    FFMPEG = Path("/usr/local/bin/ffmpeg")


def stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)


def percentile(values: list[int], p: float) -> int:
    """Nearest-rank percentile; with three trials p95 is the maximum."""
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int((p * len(ordered)) + 0.999999)))
    return ordered[rank - 1]


def run_trial(playwright, origin: str, wav: Path, number: int) -> dict:
    # A newly launched browser process resets Chromium's file-backed virtual mic
    # to the beginning for every trial; a new page alone does not guarantee this.
    browser = playwright.chromium.launch(
        headless=True, executable_path=str(BRAVE),
        args=["--no-sandbox", "--disable-dev-shm-usage",
              "--use-fake-device-for-media-stream",
              "--use-fake-ui-for-media-stream",
              "--use-file-for-fake-audio-capture=" + str(wav)])
    context = browser.new_context(permissions=["microphone"],
                                  viewport={"width": 1200, "height": 900})
    page = context.new_page()
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    try:
        page.goto(origin, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_function(
            "document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')",
            timeout=60000)
        page.locator("#consent").check()
        click_started = time.monotonic()
        page.locator("#startBtn").click()
        page.wait_for_function(
            "document.querySelector('#counter').textContent !== '0 passages'",
            timeout=45000)
        transcript_visible = time.monotonic()
        page.wait_for_function(
            "document.querySelector('#cueTitle').textContent !== 'Waiting for conversation'",
            timeout=10000)
        cue_visible = time.monotonic()
        transcript = page.locator("#transcript").inner_text()
        cue = page.locator("#cueTitle").inner_text()
        if not transcript.strip() or not cue.strip():
            raise RuntimeError("trial %d: visible transcript or local cue was empty" % number)
        result = {
            "trial": number,
            "click_to_visible_transcript_ms": round((transcript_visible-click_started)*1000),
            "click_to_visible_local_cue_ms": round((cue_visible-click_started)*1000),
            "visible_transcript_chars": len(transcript),
            "visible_cue_chars": len(cue),
            "page_errors": page_errors,
        }
        try:
            page.locator("#stopBtn").click(timeout=2000)
            page.wait_for_function(
                "document.querySelector('#status').textContent.includes('NOT LISTENING')",
                timeout=5000)
        except Exception as error:
            raise RuntimeError("trial %d: capture cleanup did not confirm Stop" % number) from error
        if page_errors:
            raise RuntimeError("trial %d: browser page errors: %s" % (number, page_errors))
        return result
    finally:
        context.close()
        browser.close()


def main() -> int:
    if sys.platform != "darwin" or not BRAVE.is_file() or not SAY.is_file() or not FFMPEG.is_file():
        print("BLOCKED: requires macOS, installed Brave, say, and FFmpeg")
        return 2
    qa_python = os.environ.get("LENS_QA_PYTHON")
    if qa_python:
        executable = Path(qa_python)
        if not executable.is_file():
            print("BLOCKED: LENS_QA_PYTHON does not point to a Python executable")
            return 2

    phrase = ("This is a local Conversation Lens latency check. "
              "Please confirm the delivery date and next step.")
    server = None
    browser = None
    try:
        with tempfile.TemporaryDirectory(prefix="lens-cue-latency-") as tmp:
            temp = Path(tmp)
            source = temp / "generated-speech.aiff"
            wav = temp / "virtual-microphone.wav"
            subprocess.run([str(SAY), "-v", "Alex", "-r", "185", phrase,
                            "-o", str(source)], check=True, timeout=25,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([str(FFMPEG), "-nostdin", "-loglevel", "error", "-y",
                            "-i", str(source), "-af", "apad=pad_dur=2",
                            "-t", "9", "-ac", "1", "-ar", "16000",
                            "-c:a", "pcm_s16le", str(wav)], check=True, timeout=25,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            env = dict(os.environ)
            server = subprocess.Popen(
                [sys.executable, str(SERVER), "--no-browser", "--port", "0"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                bufsize=1, env=env)
            readable, _, _ = select.select([server.stdout], [], [], 60)
            if not readable:
                raise RuntimeError("local app server did not announce readiness")
            ready = server.stdout.readline().strip()
            match = re.search(r"http://127\.0\.0\.1:(\d+)/", ready)
            if not match:
                raise RuntimeError("local app server failed to start: " + ready[:240])
            origin = "http://127.0.0.1:" + match.group(1)

            trials = []
            with sync_playwright() as p:
                for number in range(1, 4):
                    trials.append(run_trial(p, origin, wav, number))
            transcript_values = [t["click_to_visible_transcript_ms"] for t in trials]
            cue_values = [t["click_to_visible_local_cue_ms"] for t in trials]
            result = {
                "status": "PASS",
                "input": "generated speech through Brave virtual microphone",
                "endpoint": "real local Conversation Lens server and installed local models",
                "trial_count": len(trials),
                "trials": trials,
                "summary_ms": {
                    "click_to_visible_transcript_median": percentile(transcript_values, 0.50),
                    "click_to_visible_transcript_p95": percentile(transcript_values, 0.95),
                    "click_to_visible_local_cue_median": percentile(cue_values, 0.50),
                    "click_to_visible_local_cue_p95": percentile(cue_values, 0.95),
                },
                "limitations": ["not a physical microphone", "one generated phrase replayed in three fresh browser processes",
                                "three-trial p95 equals the maximum and is not a stable population estimate",
                                "not natural-speech accuracy"],
            }
            print(json.dumps(result, sort_keys=True))
            return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)[:500]}, sort_keys=True))
        return 2
    finally:
        if browser is not None:
            browser.close()
        if server is not None:
            stop(server)


if __name__ == "__main__":
    raise SystemExit(main())

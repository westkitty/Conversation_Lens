#!/usr/bin/env python3
"""Physical-microphone Stop -> Keep acceptance check for macOS Brave.

Plays a generated local test phrase through the Mac speakers into the real
selected microphone. No fake audio device is configured. Audio and transcript
remain temporary; the script erases the session and stops its local server.
Run only in a quiet room, with no other people being recorded.
"""
from __future__ import annotations

import argparse
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
BRAVE = Path(os.environ.get(
    "LENS_BROWSER_EXECUTABLE",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"))
SAY = Path("/usr/bin/say")
AFPLAY = Path("/usr/bin/afplay")


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-local-mic-test", action="store_true",
                        help="confirm this test may capture the generated phrase locally")
    args = parser.parse_args()
    if not args.confirm_local_mic_test:
        parser.error("pass --confirm-local-mic-test only when the Mac is in a quiet room")
    if sys.platform != "darwin" or not BRAVE.is_file() or not SAY.is_file() or not AFPLAY.is_file():
        print(json.dumps({"status": "BLOCKED", "reason": "macOS, Brave, say, and afplay are required"}))
        return 2

    phrase = ("This is a local test recording. The next step is to review the delivery date. "
              "Please confirm the schedule.")
    server: subprocess.Popen[str] | None = None
    browser = None
    player: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="lens-physical-keep-") as temp_name:
            temp = Path(temp_name)
            generated = temp / "local-test-phrase.aiff"
            subprocess.run([str(SAY), "-v", "Alex", "-r", "175", phrase,
                            "-o", str(generated)], check=True, timeout=20,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            server = subprocess.Popen(
                [sys.executable, str(APP / "server.py"), "--no-browser", "--port", "0"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                bufsize=1, env=dict(os.environ))
            readable, _, _ = select.select([server.stdout], [], [], 60)
            if not readable:
                raise RuntimeError("local server did not announce readiness")
            ready = server.stdout.readline().strip()
            match = re.search(r"http://127\.0\.0\.1:(\d+)/", ready)
            if not match:
                raise RuntimeError("local server failed to start: " + ready[:240])
            origin = "http://127.0.0.1:" + match.group(1)

            with sync_playwright() as playwright:
                # Real hardware input: deliberately omit Chromium's fake-device flag.
                browser = playwright.chromium.launch(
                    headless=False, executable_path=str(BRAVE),
                    args=["--no-sandbox", "--disable-dev-shm-usage"])
                context = browser.new_context(permissions=["microphone"],
                                              viewport={"width": 1200, "height": 900})
                page = context.new_page()
                errors: list[str] = []
                dialogs: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.add_init_script("""window.__lensMaxMicLevel=0;
                    setInterval(()=>{const rail=document.querySelector('#levelRail');
                    const value=Number(rail?.getAttribute('aria-valuenow')||0);
                    window.__lensMaxMicLevel=Math.max(window.__lensMaxMicLevel,value)},25);""")

                def accept_test_disposition(dialog) -> None:
                    dialogs.append(dialog.message[:100])
                    dialog.accept()

                page.on("dialog", accept_test_disposition)
                page.goto(origin, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_function(
                    "document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')",
                    timeout=60000)
                page.locator("#consent").check()
                page.locator("#pcmMode").check()
                page.locator("#pcmEditHold").check()
                page.locator("#startBtn").click()
                page.wait_for_function(
                    "document.querySelector('#statusText').textContent==='LOCAL MIC ACTIVE / UNVERIFIED'",
                    timeout=20000)
                devices = page.evaluate("""async () => (await navigator.mediaDevices.enumerateDevices())
                    .filter(device => device.kind === 'audioinput' && device.label)
                    .map(device => device.label)""")
                if not devices:
                    raise RuntimeError("no real audio-input device label was exposed after permission")

                player = subprocess.Popen([str(AFPLAY), str(generated)],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
                page.wait_for_function(
                    "document.querySelector('#pcmEditWindow').options.length > 0",
                    timeout=25000)
                player.wait(timeout=20)
                max_level = page.evaluate("() => window.__lensMaxMicLevel")
                if max_level <= 8:
                    raise RuntimeError("real microphone meter did not register the test phrase")
                held_count = page.locator("#pcmEditWindow option").count()
                if held_count < 1:
                    raise RuntimeError("no held PCM window was available for Stop/Keep")

                page.locator("#stopBtn").click()
                page.wait_for_function(
                    "document.querySelector('#statusText').textContent==='NOT LISTENING' && "
                    "document.querySelector('#counter').textContent!=='0 passages'",
                    timeout=60000)
                transcript = page.locator("#transcript").inner_text().lower()
                terms = ("next", "step", "review", "delivery", "date", "confirm", "schedule")
                matched_terms = sum(1 for term in terms if term in transcript)
                if matched_terms < 2:
                    raise RuntimeError("a Keep result appeared, but fewer than two test-phrase terms were recognized")
                if not any("Keep pending audio window" in message for message in dialogs):
                    raise RuntimeError("Stop did not show a per-window Keep decision")
                if errors:
                    raise RuntimeError("browser page errors occurred: " + "; ".join(errors[:3]))

                # The only captured content is generated by this test; erase it before exit.
                page.locator("#eraseAllBtn").click()
                page.wait_for_function("document.querySelector('#counter').textContent==='0 passages'",
                                       timeout=10000)
                report = {
                    "status": "PASS",
                    "input": "physical Mac audio-input device; no fake-device flag",
                    "input_devices": devices,
                    "peak_input_meter": max_level,
                    "pcm_windows_kept": held_count,
                    "phrase_terms_matched": matched_terms,
                    "stop_keep_transcript": True,
                    "session_erased": True,
                    "page_errors": errors,
                }
                print(json.dumps(report, sort_keys=True))
                context.close()
                browser.close()
                browser = None
                return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)[:500]}, sort_keys=True))
        return 2
    finally:
        if player is not None and player.poll() is None:
            player.terminate()
            try:
                player.wait(timeout=2)
            except subprocess.TimeoutExpired:
                player.kill()
        if browser is not None:
            browser.close()
        stop_process(server)


if __name__ == "__main__":
    raise SystemExit(main())

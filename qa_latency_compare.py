#!/usr/bin/env python3
"""Matched local Whisper/speaker HTTP latency comparison against origin/main.

Runs the same generated speech clip through the historical baseline and current
production server revisions on this Mac, alternating request order. Only aggregate
latency and synthetic-text error metrics are written; clip and recognized words
remain in a temporary directory / process memory. No browser or Ollama request is
made. This measures local transcription turnaround, not input-to-visible-cue time.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import signal
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import wave
from io import BytesIO

ROOT = pathlib.Path(__file__).parent
APP = ROOT / "Conversation_Lens_Intelligent_Speaker_v6"
SPEC = importlib.util.spec_from_file_location("lens_current_latency", APP / "server.py")
CURRENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CURRENT)
WORDS = (
    "This synthetic local test compares transcription turnaround on the same "
    "MacBook hardware, using the installed Whisper model and the same generated audio."
)


def http(url, body=None, headers=None, timeout=65):
    req = urllib.request.Request(url, data=body, headers=headers or {},
                                 method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {"error": "HTTP error without JSON body"}
        return error.code, payload


def normalize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def edit_distance(left, right):
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def generate_clip(directory):
    aiff = directory / "latency-speech.aiff"
    webm = directory / "latency-speech.webm"
    subprocess.run(["/usr/bin/say", "-v", "Alex", "-r", "178", WORDS,
                    "-o", str(aiff)], check=True, timeout=25,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([str(CURRENT.FFMPEG_BIN), "-nostdin", "-loglevel", "error", "-y",
                    "-i", str(aiff), "-t", "9", "-c:a", "libopus", "-b:a", "32k",
                    str(webm)], check=True, timeout=25,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    payload = webm.read_bytes()
    if len(payload) < 500:
        raise RuntimeError("Synthetic audio is below the production upload minimum")
    return payload


def extract_baseline(revision, destination):
    archive = subprocess.check_output([
        "git", "archive", "--format=tar", revision,
        "Conversation_Lens_Intelligent_Speaker_v6",
    ], cwd=ROOT)
    with tarfile.open(fileobj=BytesIO(archive), mode="r:") as tar:
        for member in tar.getmembers():
            parts = pathlib.PurePosixPath(member.name).parts
            if (not parts or parts[0] != "Conversation_Lens_Intelligent_Speaker_v6" or
                    ".." in parts or
                    not (member.isfile() or member.isdir())):
                raise RuntimeError("Baseline archive contains an unexpected file type or path")
        tar.extractall(destination)
    return destination / "Conversation_Lens_Intelligent_Speaker_v6" / "server.py"


def launch(server_path):
    env = dict(__import__("os").environ)
    env.update({
        "LENS_WHISPER_MODEL": str(CURRENT.WHISPER_MODEL),
        "LENS_WHISPER_BIN": str(CURRENT.WHISPER_BIN),
        "LENS_SPEAKER_HOME": str(CURRENT.SPEAKER_HOME),
        "LENS_SPEAKER_PYTHON": str(CURRENT.SPEAKER_PYTHON),
        "LENS_SPEAKER_MODEL": str(CURRENT.SPEAKER_MODEL),
    })
    process = subprocess.Popen(
        [sys.executable, str(server_path), "--no-browser", "--port", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        env=env,
    )
    import select
    readable, _, _ = select.select([process.stdout], [], [], 40)
    if not readable:
        process.terminate()
        raise RuntimeError("Server did not announce readiness within 40 seconds")
    line = process.stdout.readline().strip()
    match = re.search(r"http://127\.0\.0\.1:(\d+)/", line)
    if not match:
        process.terminate()
        try:
            remainder = process.communicate(timeout=5)[0]
        except subprocess.TimeoutExpired:
            process.kill()
            remainder = process.communicate()[0]
        raise RuntimeError("Server failed to start: %s %s" % (line, remainder[:2000]))
    return process, "http://127.0.0.1:%s" % match.group(1)


def capture_headers(base):
    code, status = http(base + "/api/status")
    if code != 200 or not status.get("stt", {}).get("ready"):
        raise RuntimeError("Local Whisper is unavailable in benchmark server")
    headers = {"X-Lens-Token": status["token"], "Origin": base,
               "X-Lens-Protocol": str(status.get("protocol", 1)),
               "Content-Type": "application/json"}
    code, body = http(base + "/api/capture/open", b'{"consent":true}', headers)
    if code != 200 or not body.get("capture"):
        raise RuntimeError("Could not start isolated benchmark capture")
    return headers, body["capture"]


def one_request(base, headers, capture, audio, number):
    started = time.monotonic()
    code, body = http(base + "/api/transcribe", audio,
                      {**headers, "Content-Type": "audio/webm",
                       "X-Lens-Capture-Session": capture,
                       "X-Lens-Window-ID": "latency_%04d" % number,
                       "X-Lens-Language": "en"})
    elapsed = time.monotonic() - started
    if code != 200 or body.get("engine") not in ("whisper-cpp", None) or len(body.get("text", "")) < 15:
        raise RuntimeError("Benchmark transcription failed (HTTP %d)" % code)
    error_rate = edit_distance(normalize(WORDS), normalize(body["text"])) / max(1, len(normalize(WORDS)))
    return elapsed, error_rate


def stop(process):
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def percentile(values, p):
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1,
                             int((len(ordered) - 1) * p))], 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="origin/main")
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--report", type=pathlib.Path,
                        default=pathlib.Path(tempfile.gettempdir()) /
                        ("conversation-lens-latency-%d.json" % int(time.time())))
    args = parser.parse_args()
    if sys.platform != "darwin":
        print("BLOCKED: matched speech benchmark is scoped to the MacBook runtime")
        return 2
    if args.repetitions < 5:
        parser.error("Use at least five measured repetitions per version")
    baseline_sha = subprocess.check_output(
        ["git", "rev-parse", args.baseline], cwd=ROOT, text=True).strip()
    current_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not CURRENT.whisper_status().get("ready") or not CURRENT.speaker_status().get("ready"):
        print("BLOCKED: local Whisper and speaker models must both be ready")
        return 2

    with tempfile.TemporaryDirectory(prefix="lens-latency-compare-") as temp:
        temp = pathlib.Path(temp)
        audio = generate_clip(temp)
        baseline_server = extract_baseline(args.baseline, temp)
        processes = []
        baselines, currents, baseline_wer, current_wer = [], [], [], []
        headers_by_name, captures = {}, {}
        try:
            p0, u0 = launch(baseline_server)
            processes.append(p0)
            p1, u1 = launch(APP / "server.py")
            processes.append(p1)
            for name, base in (("baseline", u0), ("current", u1)):
                headers, capture = capture_headers(base)
                headers_by_name[name] = (base, headers)
                captures[name] = capture

            # Equal warm-up count; excluded from measurements.
            for name in ("baseline", "current"):
                base, headers = headers_by_name[name]
                for i in range(3):
                    one_request(base, headers, captures[name], audio, i + 1)

            for repetition in range(args.repetitions):
                order = ("baseline", "current") if repetition % 2 == 0 else ("current", "baseline")
                for name in order:
                    base, headers = headers_by_name[name]
                    elapsed, wer = one_request(base, headers, captures[name], audio,
                                               repetition + 100)
                    if name == "baseline":
                        baselines.append(elapsed)
                        baseline_wer.append(wer)
                    else:
                        currents.append(elapsed)
                        current_wer.append(wer)
                print("LATENCY_PAIR %d/%d baseline=%.3fs current=%.3fs" %
                      (repetition + 1, args.repetitions, baselines[-1], currents[-1]),
                      flush=True)

            bmed, cmed = statistics.median(baselines), statistics.median(currents)
            summary = {
                "result": "PASS",
                "baselineRevision": args.baseline,
                "baselineSha": baseline_sha,
                "currentSha": current_sha,
                "baselineRepetitions": len(baselines),
                "currentRepetitions": len(currents),
                "baselineMedianSeconds": round(bmed, 3),
                "currentMedianSeconds": round(cmed, 3),
                "medianChangePercent": round((cmed - bmed) / bmed * 100, 2),
                "baselineP95Seconds": percentile(baselines, .95),
                "currentP95Seconds": percentile(currents, .95),
                "baselineMeanWer": round(statistics.mean(baseline_wer), 4),
                "currentMeanWer": round(statistics.mean(current_wer), 4),
                "scope": "localhost POST /api/transcribe with identical synthetic WebM; local Whisper and speaker worker",
                "limitations": ["synthetic single-voice speech", "no browser input-to-visible-cue timing", "one MacBook and installed model"],
                "syntheticContentSaved": False,
            }
            with args.report.open("x", encoding="utf-8") as destination:
                destination.write(json.dumps(summary, indent=2) + "\n")
            print("LATENCY_SUMMARY " + json.dumps(summary, separators=(",", ":")), flush=True)
            return 0
        finally:
            for name, (base, headers) in headers_by_name.items():
                http(base + "/api/capture/close",
                     json.dumps({"capture": captures[name]}).encode(), headers)
                http(base + "/api/session/erase", b'{"confirm":true}', headers)
            for process in processes:
                stop(process)


if __name__ == "__main__":
    raise SystemExit(main())

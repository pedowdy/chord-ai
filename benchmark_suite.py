#!/usr/bin/env python3
"""Run the five retained chord-detector benchmarks and emit compact results."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SONGS = {
    "Let It Be": "test 7a.mp3",
    "Day 1": "day1_intro.mp3",
    "Stand by Me": "stand_by_me.mp3",
    "Just the Two of Us": "just_the_two_of_us.mp3",
    "Hotel California": "hotel_california.mp3",
}

METRIC_PATTERN = re.compile(
    r"^(Root accuracy|Base chord accuracy|Exact chord accuracy):\s+([0-9.]+)%$",
    re.MULTILINE,
)
METRIC_NAMES = {
    "Root accuracy": "root",
    "Base chord accuracy": "base",
    "Exact chord accuracy": "exact",
}


def run_suite(code_dir: Path, media_dir: Path):
    results = {}
    with tempfile.TemporaryDirectory(prefix="chord-ai-numba-") as cache_dir:
        env = os.environ.copy()
        env["NUMBA_CACHE_DIR"] = cache_dir
        env["PYTHONPYCACHEPREFIX"] = cache_dir
        for song, filename in SONGS.items():
            command = [
                sys.executable,
                str(code_dir / "chord_detector.py"),
                str(media_dir / filename),
            ]
            completed = subprocess.run(
                command,
                # Keep fallback annotation lookup beside the audio even when
                # candidate code is running from a disposable directory.
                cwd=media_dir,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"{song} failed with exit code {completed.returncode}:\n"
                    f"{completed.stdout[-4000:]}"
                )
            metrics = {
                METRIC_NAMES[name]: float(value)
                for name, value in METRIC_PATTERN.findall(completed.stdout)
            }
            if set(metrics) != {"root", "base", "exact"}:
                raise RuntimeError(f"Could not parse metrics for {song}")
            results[song] = metrics
    return results


def print_table(results):
    print(f"{'Song':24} {'Root':>7} {'Base':>7} {'Exact':>7}")
    for song, metrics in results.items():
        print(
            f"{song:24} {metrics['root']:6.1f}% "
            f"{metrics['base']:6.1f}% {metrics['exact']:6.1f}%"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--media-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = run_suite(args.code_dir.resolve(), args.media_dir.resolve())
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_table(results)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Evaluate one patch safely against the retained five-song baseline."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from benchmark_suite import run_suite


ROOT = Path(__file__).resolve().parent
EXPERIMENTS = ROOT / "experiments"
BASELINE = EXPERIMENTS / "baseline.json"
LEDGER = EXPERIMENTS / "log.md"
METRICS = ("root", "base", "exact")


def digest(paths):
    result = {}
    for path in paths:
        data = path.read_bytes()
        result[path.name] = hashlib.sha256(data).hexdigest()
    return result


def decision(baseline, candidate):
    regressions = []
    improvements = []
    for song, old_metrics in baseline.items():
        for metric in METRICS:
            delta = round(candidate[song][metric] - old_metrics[metric], 10)
            if delta < 0:
                regressions.append((song, metric, delta))
            elif delta > 0:
                improvements.append((song, metric, delta))
    keep = not regressions and bool(improvements)
    reason = (
        "at least one metric improved and no song/metric regressed"
        if keep
        else "regression detected" if regressions else "no measured improvement"
    )
    return keep, reason, regressions, improvements


def append_log(name, hypothesis, patch, baseline, candidate, verdict, reason):
    lines = [
        "",
        f"## {datetime.now(timezone.utc).isoformat(timespec='seconds')} — {name}",
        "",
        f"- Hypothesis: {hypothesis}",
        f"- Patch: `{patch.name}`",
        f"- Verdict: **{verdict}** — {reason}",
        "",
        "| Song | Root | Base | Exact |",
        "| --- | ---: | ---: | ---: |",
    ]
    for song in baseline:
        cells = []
        for metric in METRICS:
            old = baseline[song][metric]
            new = candidate[song][metric]
            cells.append(f"{old:.1f} → {new:.1f} ({new-old:+.1f})")
        lines.append(f"| {song} | {' | '.join(cells)} |")
    with LEDGER.open("a") as handle:
        handle.write("\n".join(lines) + "\n")


def initialize():
    EXPERIMENTS.mkdir(exist_ok=True)
    results = run_suite(ROOT, ROOT)
    BASELINE.write_text(json.dumps(results, indent=2) + "\n")
    if not LEDGER.exists():
        LEDGER.write_text(
            "# Chord AI experiment log\n\n"
            "Acceptance gate: keep only when at least one of the 15 benchmark "
            "metrics improves and none regress. Every trial is logged.\n\n"
            "The initial baseline includes the retained maj7-only hierarchy.\n"
        )
    print(json.dumps(results, indent=2))


def trial(args):
    baseline = json.loads(BASELINE.read_text())
    source_files = [ROOT / "chord_detector.py", ROOT / "evaluate.py"]
    before = digest(source_files)
    with tempfile.TemporaryDirectory(prefix="chord-ai-trial-") as temp:
        candidate_dir = Path(temp)
        for path in source_files + [ROOT / "benchmark_suite.py"]:
            shutil.copy2(path, candidate_dir / path.name)
        applied = subprocess.run(
            ["git", "apply", "--unsafe-paths", str(args.patch.resolve())],
            cwd=candidate_dir,
            text=True,
            capture_output=True,
        )
        if applied.returncode:
            raise SystemExit(f"Patch did not apply in the disposable trial:\n{applied.stderr}")
        candidate = run_suite(candidate_dir, ROOT)
    keep, reason, regressions, improvements = decision(baseline, candidate)
    verdict = "KEEP" if keep else "REVERT"
    append_log(
        args.name, args.hypothesis, args.patch, baseline, candidate, verdict, reason
    )
    print(f"{verdict}: {reason}")
    for song, metric, delta in regressions + improvements:
        print(f"  {song} {metric}: {delta:+.1f}")
    if args.accept:
        if not keep:
            raise SystemExit("Rejected trial was not applied.")
        if digest(source_files) != before:
            raise SystemExit("Source changed during the trial; accepted patch was not applied.")
        subprocess.run(["git", "apply", str(args.patch.resolve())], cwd=ROOT, check=True)
        BASELINE.write_text(json.dumps(candidate, indent=2) + "\n")
        print("Accepted patch applied; baseline advanced.")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    run = sub.add_parser("trial")
    run.add_argument("--name", required=True)
    run.add_argument("--hypothesis", required=True)
    run.add_argument("--patch", required=True, type=Path)
    run.add_argument("--accept", action="store_true")
    args = parser.parse_args()
    if args.command == "init":
        initialize()
    else:
        trial(args)


if __name__ == "__main__":
    main()

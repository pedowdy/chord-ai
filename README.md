# Chord AI

Chord AI is an experimental Python project for automatically transcribing chords from audio.

Instead of treating each audio frame independently, the detector combines harmonic evidence, bass information, key context, and sequence decoding to estimate a more musically plausible chord progression over time.

The project is currently focused on improving chord-recognition accuracy through controlled benchmarking and iterative experiments.

## Features

- Audio analysis using `librosa`
- Chroma-based harmonic feature extraction
- Chord-template matching
- Bass-note detection
- Key estimation
- Key-aware chord scoring
- Viterbi sequence decoding
- Minimum-duration filtering
- Benchmark evaluation against manually annotated chord progressions
- Experiment logging and regression testing

## Supported Chord Types

The current detector recognizes:

- Major
- Minor
- Major 6
- Minor 6
- Dominant 7
- Major 7
- Minor 7

Support for more chord families may be added as the detector develops.

## How It Works

At a high level, the current system works like this:

1. Load an audio file.
2. Extract chroma and frequency information.
3. Estimate harmonic evidence for possible chord roots and chord types.
4. Detect bass-note evidence.
5. Estimate the musical key.
6. Adjust chord scores using key context.
7. Decode the most likely chord sequence using Viterbi smoothing.
8. Remove implausibly short detections.
9. Compare the result against manually annotated benchmark data.

This makes the detector more than a simple frame-by-frame chord-template matcher.

## Benchmarking

Development is benchmark-driven.

The current benchmark set includes annotated sections from:

- **Stand by Me** — Ben E. King
- **Just the Two of Us** — Grover Washington Jr. feat. Bill Withers
- **Hotel California** — Eagles

The original commercial audio is **not included in this repository**.

Only manually created annotation and evaluation data are stored here.

## Evaluation Philosophy

Detector changes are tested against the benchmark suite before being retained.

The current acceptance rule is:

> A change is kept only when at least one benchmark metric improves and no benchmark metric regresses.

This is intended to reduce overfitting to individual songs and make improvements more measurable.

Evaluation includes measurements related to:

- Root accuracy
- Base chord accuracy
- Exact chord accuracy
- Song-level benchmark performance

Experiment results and retained changes are documented in the `experiments/` directory.

## Project Structure

```text
chord-ai/
├── chord_detector.py
├── evaluate.py
├── benchmark_suite.py
├── experiment_loop.py
│
├── stand_by_me.txt
├── just_the_two_of_us.txt
├── hotel_california.txt
│
├── experiments/
│   ├── README.md
│   ├── baseline.json
│   └── log.md
│
├── .gitignore
└── README.md

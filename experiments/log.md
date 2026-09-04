# Chord AI experiment log

Acceptance gate: keep only when at least one of the 15 benchmark metrics improves and none regress. Every trial is logged.

The initial baseline includes the retained maj7-only hierarchy.

## 2026-08-31 — Remaining-error diagnostic: Just the Two of Us

- Status: **DIAGNOSTIC ONLY** — no detector behavior changed.
- Reason selected: this song has the weakest retained result (45.9 root / 41.3 base / 8.3 exact).
- Dominant pattern: the remaining errors are primarily root/transition errors, not same-root extension selection. The decoded sequence repeatedly crosses between C#/C/F material at the wrong times or roots.
- Representative spans: 0.000–0.500 is Dm instead of C#maj7; 1.500–2.125 is C#maj7 instead of C7; 4.125–4.500 is C#6 instead of Fm7.
- Only one final same-root wrong-family span remains: 19.500–20.000, F instead of Fm7.
- Implication: do not tune extension-family eligibility next. Diagnose root emissions and transition timing on the repeated C#maj7 → C7 → Fm7 cycle before proposing a change.

## 2026-08-31 — Initial root boundary correction

- Hypothesis: extend the existing early-root local-evidence correction to frame zero, preventing Viterbi from rewriting a locally supported opening root.
- Verdict: **REVERT** — Just the Two of Us improved, but Day 1 regressed.
- Project behavior changed: **No**. The candidate ran only in a disposable copy.

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 88.5 (+0.0) |
| Day 1 | 91.2 → 89.7 (-1.5) | 91.2 → 89.7 (-1.5) | 61.0 → 59.6 (-1.4) |
| Stand by Me | 83.8 → 83.8 (+0.0) | 83.8 → 83.8 (+0.0) | 71.5 → 71.5 (+0.0) |
| Just the Two of Us | 45.9 → 48.6 (+2.7) | 41.3 → 44.0 (+2.7) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31 — Just the Two of Us ground-truth timing audit

- Status: **DIAGNOSTIC ONLY** — no detector, annotation, evaluator, or parameter changes.
- Scope: all 11 annotated chord boundaries, using harmonic chroma, outgoing/incoming chord contrast, local root evidence, bass chroma, and spectral/onset evidence in ±0.75-second windows.
- Finding: annotations are generally centered within the acoustic transition ranges. Boundaries at 6.105, 9.964, and 11.087 are gradual/ambiguous, but no boundary strongly supports a materially different point timestamp.
- Repetition: no accumulating timing drift across the repeated C#maj7 → C7 → Fm7 cycles.
- Detector relation: most apparent C#/C/F timing errors are genuine early, late, or wrong root-path decisions. Annotation ambiguity does not explain the large wrong-root spans.
- Evaluator: ±0.30 seconds is reasonable for this material and does not mask a systematic annotation problem.
- Disposable counterfactual: no strongly supported corrections qualified, so the temporary annotation remained identical. Metrics stayed 67.9 root / 60.6 base / 8.3 exact.
- Recommendation: retain the annotations; optionally perform a future expert listening pass on the three ambiguous boundaries. Continue root-path/cleanup architecture work and keep parameter searching paused.

## 2026-08-31 — JTOU root-path and cleanup attribution

- Status: **DIAGNOSTIC ONLY** — no detector, scoring, transition, cleanup, annotation, or evaluator changes.
- Retained JTOU baseline confirmed: 67.9 root / 60.6 base / 8.3 exact.
- Remaining evaluated root errors: 35 frames across seven spans.
- Local emission winner is wrong on 27/35 frames. The annotated root is already locally highest on 8/35 frames.
- All eight locally recoverable frames reach the correct Viterbi root but are erased by full-chord minimum-duration cleanup.
- Persistent early-root correction changes none of the remaining wrong-root spans. Final quality selection cannot change root.
- Counterfactual A, no duration cleanup: JTOU falls to 54.1 / 48.6 / 9.2 and causes major regressions elsewhere. Duration cleanup is essential globally.
- Counterfactual B, independent framewise roots: JTOU remains 67.9 / 60.6 / 8.3 after downstream cleanup, while Let It Be and Day 1 regress. Viterbi transition costs are not the next target.
- Root margins across final wrong frames: annotated root stronger on 12, near-tied on 1, genuinely weaker on 22.
- Recommended next A/B, not implemented: preserve a contiguous same-root run that already meets minimum duration from being erased solely because its individual chord-quality segments are short. Keep all existing thresholds and other cleanup behavior.

## 2026-08-31T11:33:52+00:00 — Persistent initial-root correction

- Hypothesis: Apply the existing local-evidence correction at frame zero only when the competing opening root persists for at least three consecutive frames.
- Patch: `initial-root-correction.patch`
- Verdict: **KEEP** — at least one metric improved and no song/metric regressed

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 88.5 (+0.0) |
| Day 1 | 91.2 → 91.2 (+0.0) | 91.2 → 91.2 (+0.0) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 83.8 → 83.8 (+0.0) | 83.8 → 83.8 (+0.0) | 71.5 → 71.5 (+0.0) |
| Just the Two of Us | 45.9 → 48.6 (+2.7) | 41.3 → 44.0 (+2.7) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T11:34:18+00:00 — Persistent initial-root correction

- Hypothesis: Apply the existing local-evidence correction at frame zero only when the competing opening root persists for at least three consecutive frames.
- Patch: `initial-root-correction.patch`
- Verdict: **KEEP** — at least one metric improved and no song/metric regressed

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 88.5 (+0.0) |
| Day 1 | 91.2 → 91.2 (+0.0) | 91.2 → 91.2 (+0.0) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 83.8 → 83.8 (+0.0) | 83.8 → 83.8 (+0.0) | 71.5 → 71.5 (+0.0) |
| Just the Two of Us | 45.9 → 48.6 (+2.7) | 41.3 → 44.0 (+2.7) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T11:57:44+00:00 — Modest extension-penalty reduction

- Hypothesis: Reduce the universal extension penalty from 0.035 to 0.025 so marginal genuine C7/Fm7 evidence can survive without removing the regularizer.
- Patch: `extension-penalty-0025.patch`
- Verdict: **REVERT** — regression detected

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 88.5 (+0.0) |
| Day 1 | 91.2 → 91.2 (+0.0) | 91.2 → 91.2 (+0.0) | 61.0 → 63.2 (+2.2) |
| Stand by Me | 83.8 → 83.8 (+0.0) | 83.8 → 83.8 (+0.0) | 71.5 → 25.4 (-46.1) |
| Just the Two of Us | 48.6 → 43.1 (-5.5) | 44.0 → 38.5 (-5.5) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 83.9 (-1.7) |

### Extension-margin diagnostic conclusion

- Day 1 annotated Bmaj7 evidence is already strong: mean extension-over-triad margin +0.1021; 39/48 frames win before sequence cleanup.
- Just the Two of Us annotated C#maj7 is marginal: mean +0.0157; 18/36 frames win.
- Its annotated C7 and Fm7 evidence is weak relative to the plain triads: means -0.0352 and -0.0362, respectively.
- The rejected penalty experiment shows this cannot be repaired safely with a global extension adjustment. The 0.035 regularizer is essential to Stand by Me and materially protects Hotel California.
- Next direction: retain the extension penalty and investigate root/sequence architecture or extension evidence local to the decoded root, rather than global score tuning.

## 2026-08-31T12:00:59+00:00 — Triad-only root emissions

- Hypothesis: Decode root identity from same-root major/minor triads only, then select extensions afterward using the retained quality logic.
- Patch: `triad-only-root-emissions.patch`
- Verdict: **REVERT** — regression detected

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 95.7 (+1.5) | 94.2 → 95.7 (+1.5) | 88.5 → 94.7 (+6.2) |
| Day 1 | 91.2 → 77.2 (-14.0) | 91.2 → 75.0 (-16.2) | 61.0 → 58.1 (-2.9) |
| Stand by Me | 83.8 → 75.4 (-8.4) | 83.8 → 73.8 (-10.0) | 71.5 → 53.1 (-18.4) |
| Just the Two of Us | 48.6 → 71.6 (+23.0) | 44.0 → 65.1 (+21.1) | 8.3 → 7.3 (-1.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T12:07:29+00:00 — Capped extension lift for root emissions

- Hypothesis: Limit extension-driven root emission to 0.250 above the best same-root triad, preserving useful extension evidence while preventing extreme root inflation.
- Patch: `capped-root-emissions-025.patch`
- Verdict: **REVERT** — regression detected

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 90.4 (+1.9) |
| Day 1 | 91.2 → 90.4 (-0.8) | 91.2 → 90.4 (-0.8) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 83.8 → 85.4 (+1.6) | 83.8 → 83.8 (+0.0) | 71.5 → 75.4 (+3.9) |
| Just the Two of Us | 48.6 → 67.0 (+18.4) | 44.0 → 59.6 (+15.6) | 8.3 → 7.3 (-1.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T12:15:28+00:00 — Capped extension lift at 0.275

- Hypothesis: A 0.275 cap preserves helpful Day 1 extension-root evidence while still limiting the extreme root inflation observed in Just the Two of Us.
- Patch: `capped-root-emissions-025.patch`
- Verdict: **KEEP** — at least one metric improved and no song/metric regressed

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 90.4 (+1.9) |
| Day 1 | 91.2 → 91.2 (+0.0) | 91.2 → 91.2 (+0.0) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 83.8 → 85.4 (+1.6) | 83.8 → 83.8 (+0.0) | 71.5 → 73.1 (+1.6) |
| Just the Two of Us | 48.6 → 67.9 (+19.3) | 44.0 → 60.6 (+16.6) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T12:16:17+00:00 — Capped extension lift at 0.275

- Hypothesis: A 0.275 cap preserves helpful Day 1 extension-root evidence while still limiting the extreme root inflation observed in Just the Two of Us.
- Patch: `capped-root-emissions-025.patch`
- Verdict: **KEEP** — at least one metric improved and no song/metric regressed

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 94.2 (+0.0) | 94.2 → 94.2 (+0.0) | 88.5 → 90.4 (+1.9) |
| Day 1 | 91.2 → 91.2 (+0.0) | 91.2 → 91.2 (+0.0) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 83.8 → 85.4 (+1.6) | 83.8 → 83.8 (+0.0) | 71.5 → 73.1 (+1.6) |
| Just the Two of Us | 48.6 → 67.9 (+19.3) | 44.0 → 60.6 (+16.6) | 8.3 → 8.3 (+0.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

## 2026-08-31T12:36:44+00:00 — Root-preserving duration cleanup

- Hypothesis: Prevent short quality fragments from being merged across roots when their contiguous same-root run already satisfies the existing four-frame minimum.
- Patch: `root-preserving-duration.patch`
- Verdict: **REVERT** — regression detected

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 93.8 (-0.4) | 94.2 → 93.8 (-0.4) | 90.4 → 89.9 (-0.5) |
| Day 1 | 91.2 → 92.6 (+1.4) | 91.2 → 92.6 (+1.4) | 61.0 → 61.0 (+0.0) |
| Stand by Me | 85.4 → 78.5 (-6.9) | 83.8 → 78.5 (-5.3) | 73.1 → 70.0 (-3.1) |
| Just the Two of Us | 67.9 → 57.8 (-10.1) | 60.6 → 50.5 (-10.1) | 8.3 → 7.3 (-1.0) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

### Root-preserving cleanup propagation analysis

- Target recovery: 3 of the 8 previously identified JTOU frames.
- JTOU collateral damage: 14 previously correct evaluated root frames became wrong; 39 final frames changed in total.
- Other changed final frames: Let It Be 3, Day 1 6, Stand by Me 24, Hotel California 1.
- Day 1 generalized positively (+1.4 root/base), but Let It Be, Stand by Me, and JTOU regressed.
- Cause: iterative cleanup protected noisy same-root islands as well as correct fragmented runs. Those islands altered later neighbor selection and propagated incorrect roots/boundaries.
- Decision: **REVERT**. Candidate remained disposable; retained baseline and production detector are unchanged. No tuned variant was attempted.

## 2026-08-31 — JTOU local root emission error analysis

- Status: **DIAGNOSTIC ONLY** — no detector, Viterbi, cleanup, persistence, cap, scoring, template, annotation, or evaluator changes.
- Scope: the 27 evaluated frames previously attributed to a wrong retained local root winner.
- Primary mechanisms: strong non-chord/chromatic/melody pitch energy 12; extension-driven wrong root 6; ambiguous voicing/inversion 6; weak annotated-root evidence 2; bass-driven 1; key-bonus bias 0.
- The retained 0.275 cap reduces the wrong emission on 8/27 frames and never clips the annotated root, but does not flip the winner.
- Bass strength is 1.0 on every frame by construction and is not a confidence measure. Actual top-versus-runner-up bass dominance averages 0.250 on the failures, versus 0.370–0.808 on correctly detected frames in the other songs.
- Cross-song safety: extensions are necessary for 33 correct comparison frames and bass for 68; neither should be removed or globally suppressed.
- Repeated mechanism: D/Dmaj7 competition during C# material, E/F competition during C7, and strong B/A#/C# chromatic evidence producing Bmaj7/A#m7/C#maj7 during annotated Fm7.
- Recommended next A/B, not implemented: replace tautological bass strength with `(largest − runner-up) / largest` dominance in the existing bass bonus. No threshold or other scoring change.

## 2026-08-31T13:37:27+00:00 — Bass dominance confidence

- Hypothesis: Use top-versus-runner-up bass chroma dominance as the existing bass bonus multiplier so ambiguous estimates receive less influence while decisive bass cues remain strong.
- Patch: `bass-confidence.patch`
- Verdict: **REVERT** — regression detected

| Song | Root | Base | Exact |
| --- | ---: | ---: | ---: |
| Let It Be | 94.2 → 92.3 (-1.9) | 94.2 → 92.3 (-1.9) | 90.4 → 89.4 (-1.0) |
| Day 1 | 91.2 → 79.4 (-11.8) | 91.2 → 79.4 (-11.8) | 61.0 → 57.4 (-3.6) |
| Stand by Me | 85.4 → 83.8 (-1.6) | 83.8 → 83.8 (+0.0) | 73.1 → 61.5 (-11.6) |
| Just the Two of Us | 67.9 → 62.4 (-5.5) | 60.6 → 56.0 (-4.6) | 8.3 → 2.8 (-5.5) |
| Hotel California | 98.9 → 98.9 (+0.0) | 87.9 → 87.9 (+0.0) | 85.6 → 85.6 (+0.0) |

### Bass-confidence targeted and propagation analysis

- Implementation verification: candidate strength remained in [0,1]. Ambiguous JTOU examples fell to 0.005–0.082; decisive comparison examples remained 0.619–0.915.
- Strength means, old → new: JTOU target failures 1.000 → 0.250; correct Let It Be 1.000 → 0.512; Day 1 → 0.552; Stand by Me → 0.370; Hotel California → 0.808.
- JTOU target winners changed on 8/27 frames, but only the single bass-driven frame at 9.625 became correct.
- None of 12 chromatic failures or 6 extension-driven failures were fixed; four ambiguous cases changed to another wrong root.
- Eleven previously correct evaluated JTOU local-root frames became wrong.
- Final changed frames: Let It Be 10, Day 1 46, Stand by Me 46, JTOU 46, Hotel California 0.
- Diagnosis: raw dominance is a valid confidence signal, but directly replacing the full multiplier removes bass support on which current scoring and sequence behavior rely. It exposes other wrong chroma/template candidates rather than resolving them.
- Decision: **REVERT**. Candidate was not applied; authoritative baseline unchanged. No tuned variant attempted.

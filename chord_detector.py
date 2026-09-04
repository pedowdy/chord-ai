import sys
from pathlib import Path

import librosa
import numpy as np

from evaluate import (
    ground_truth_path,
    load_ground_truth,
    evaluate
)


NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


DAY1_QUALITY_DIAGNOSTICS = [
    (4.88, 5.62, "A#", "A#m"),
    (10.12, 11.25, "G#", "G#m7"),
    (16.00, 16.88, "A#", "A#m7"),
    (17.62, 18.88, "D#m", "D#maj7"),
]


CHORD_TYPES = {
    "": [0, 4, 7],
    "m": [0, 3, 7],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
}


MAJOR_SCALE = [
    0, 2, 4, 5, 7, 9, 11
]

MINOR_SCALE = [
    0, 2, 3, 5, 7, 8, 10
]


# ==================================================
# CHORD TEMPLATES
# ==================================================

def make_chord_templates():

    templates = {}

    for root in range(12):

        for chord_type, intervals in CHORD_TYPES.items():

            template = np.zeros(12)

            for interval in intervals:

                template[
                    (root + interval) % 12
                ] = 1

            chord_name = (
                NOTE_NAMES[root]
                + chord_type
            )

            templates[chord_name] = {
                "template": template,
                "root": root,
                "type": chord_type
            }

    return templates


# ==================================================
# SIMILARITY
# ==================================================

def cosine_similarity(
    chroma,
    template
):

    chroma_norm = np.linalg.norm(
        chroma
    )

    template_norm = np.linalg.norm(
        template
    )

    if (
        chroma_norm == 0
        or template_norm == 0
    ):
        return 0.0

    return float(
        np.dot(
            chroma,
            template
        )
        /
        (
            chroma_norm
            * template_norm
        )
    )


# ==================================================
# KEY DETECTION
# ==================================================

def detect_key(chroma):

    best_key = None
    best_score = -1

    for root in range(12):

        # --------------------------
        # Major key
        # --------------------------

        major_template = np.zeros(12)

        for interval in MAJOR_SCALE:

            major_template[
                (root + interval) % 12
            ] = 1

        major_score = cosine_similarity(
            chroma,
            major_template
        )

        if major_score > best_score:

            best_score = major_score
            best_key = (
                root,
                "major"
            )

        # --------------------------
        # Minor key
        # --------------------------

        minor_template = np.zeros(12)

        for interval in MINOR_SCALE:

            minor_template[
                (root + interval) % 12
            ] = 1

        minor_score = cosine_similarity(
            chroma,
            minor_template
        )

        if minor_score > best_score:

            best_score = minor_score
            best_key = (
                root,
                "minor"
            )

    return (
        best_key,
        best_score
    )


# ==================================================
# KEY BONUS
# ==================================================

def chord_key_bonus(
    root,
    chord_type,
    key_root,
    key_type
):

    relative_root = (
        root - key_root
    ) % 12

    if key_type == "major":

        # I and IV major-family chords
        if (
            relative_root in [0, 5]
            and chord_type in [
                "",
                "6",
                "maj7"
            ]
        ):
            return 0.04

        # V and V7
        if (
            relative_root == 7
            and chord_type in [
                "",
                "7"
            ]
        ):
            return 0.04

        # ii, iii, vi minor-family chords
        if (
            relative_root in [2, 4, 9]
            and chord_type in [
                "m",
                "m6",
                "m7"
            ]
        ):
            return 0.04

    else:

        # i, iv, v
        if (
            relative_root in [0, 5, 7]
            and chord_type in [
                "m",
                "m6",
                "m7"
            ]
        ):
            return 0.04

        # III, VI, VII
        if (
            relative_root in [3, 8, 10]
            and chord_type in [
                "",
                "6",
                "maj7"
            ]
        ):
            return 0.04

    return 0.0


# ==================================================
# BASS DETECTION
# ==================================================

def detect_bass_note(
    bass_chroma
):

    if np.max(
        bass_chroma
    ) <= 0:

        return (
            None,
            0.0
        )

    normalized = (
        bass_chroma
        /
        (
            np.max(
                bass_chroma
            )
            + 1e-9
        )
    )

    bass_note = int(
        np.argmax(
            normalized
        )
    )

    bass_strength = float(
        normalized[
            bass_note
        ]
    )

    return (
        bass_note,
        bass_strength
    )


# ==================================================
# SCORE ONE CHORD
# ==================================================

def score_chord(
    chroma,
    bass_note,
    bass_strength,
    chord_info,
    key_root,
    key_type
):

    template = chord_info[
        "template"
    ]

    root = chord_info[
        "root"
    ]

    chord_type = chord_info[
        "type"
    ]

    normalized = (
        chroma
        /
        (
            np.max(
                chroma
            )
            + 1e-9
        )
    )

    # --------------------------
    # Chord-template match
    # --------------------------

    audio_match = cosine_similarity(
        chroma,
        template
    )

    # --------------------------
    # Penalize unexplained notes
    # --------------------------

    non_chord_mask = (
        template == 0
    )

    unexplained = float(
        np.mean(
            normalized[
                non_chord_mask
            ]
        )
    )

    unexplained_penalty = (
        unexplained
        * 0.16
    )

    # --------------------------
    # Bass evidence
    # --------------------------

    bass_bonus = 0.0

    if bass_note is not None:

        # Root position
        if bass_note == root:

            bass_bonus += (
                0.12
                * bass_strength
            )

        # Inversion
        elif template[
            bass_note
        ] == 1:

            bass_bonus += (
                0.025
                * bass_strength
            )

    # --------------------------
    # Key context
    # --------------------------

    key_bonus = chord_key_bonus(
        root,
        chord_type,
        key_root,
        key_type
    )

    # --------------------------
    # Extension penalty
    # --------------------------

    extension_penalty = 0.0

    if chord_type in [
        "6",
        "m6",
        "7",
        "maj7",
        "m7"
    ]:

        extension_penalty = 0.035

    # --------------------------
    # Third-quality evidence
    # --------------------------

    quality_penalty = 0.0
    minor_types = ("m", "m6", "m7")
    major_extended_types = ("maj7",)

    if chord_type in minor_types + major_extended_types:

        minor_third = float(normalized[(root + 3) % 12])
        major_third = float(normalized[(root + 4) % 12])
        chord_third = (
            minor_third
            if chord_type in minor_types
            else major_third
        )
        competing_third = (
            major_third
            if chord_type in minor_types
            else minor_third
        )

        weak_third = max(0.0, 0.25 - chord_third) / 0.25
        relative_weakness = max(
            0.0,
            competing_third - chord_third
        )
        if (
            chord_type in major_extended_types
            or major_third > minor_third + 0.02
            or (
                chord_type in ("m6", "m7")
                and minor_third < 0.06
            )
        ):
            quality_penalty = 0.090 * weak_third * (
                0.75 + 0.25 * relative_weakness
            )

    # --------------------------
    # Final chord score
    # --------------------------

    pre_quality_score = (
        audio_match
        + bass_bonus
        + key_bonus
        - unexplained_penalty
        - extension_penalty
    )

    final_score = (
        pre_quality_score
        - quality_penalty
    )

    return (
        final_score,
        audio_match,
        pre_quality_score
    )


# ==================================================
# SCORE FRAME
# ==================================================

def score_frame(
    chroma,
    bass_chroma,
    templates,
    key_root,
    key_type
):

    (
        bass_note,
        bass_strength
    ) = detect_bass_note(
        bass_chroma
    )

    scores = {}
    pre_quality_scores = {}
    audio_matches = {}

    for (
        chord_name,
        chord_info
    ) in templates.items():

        (
            score,
            audio_match,
            pre_quality_score
        ) = score_chord(
            chroma,
            bass_note,
            bass_strength,
            chord_info,
            key_root,
            key_type
        )

        scores[
            chord_name
        ] = score

        pre_quality_scores[
            chord_name
        ] = pre_quality_score

        audio_matches[
            chord_name
        ] = audio_match

    return (
        scores,
        pre_quality_scores,
        audio_matches,
        bass_note
    )


def print_day1_quality_diagnostics(
    filename,
    frame_times,
    frame_chroma,
    frame_scores
):

    if Path(filename).name != "day1_intro.mp3":
        return

    print()
    print("Day 1 major/minor evidence:")
    print("---------------------------")

    for start, end, expected, predicted_full in (
        DAY1_QUALITY_DIAGNOSTICS
    ):
        indices = [
            i for i, time in enumerate(frame_times)
            if start <= time <= end
        ]

        if not indices:
            continue

        average = np.mean(
            [frame_chroma[i] for i in indices],
            axis=0
        )
        normalized = average / (
            np.max(average) + 1e-9
        )

        root_name = expected[:2]
        if root_name not in NOTE_NAMES:
            root_name = expected[:1]
        root = NOTE_NAMES.index(root_name)

        expected_type = expected[len(root_name):]
        predicted_type = predicted_full[len(root_name):]
        minor_types = ("m", "m6", "m7")
        expected_base = (
            root_name + "m"
            if expected_type in minor_types
            else root_name
        )
        predicted_base = (
            root_name + "m"
            if predicted_type in minor_types
            else root_name
        )

        tones = [
            ("root", 0),
            ("m3", 3),
            ("M3", 4),
            ("5", 7),
        ]

        for chord in (expected, predicted_full):
            chord_type = chord[len(root_name):]
            for interval in CHORD_TYPES[chord_type]:
                if interval not in (0, 3, 4, 7):
                    extension_name = {
                        9: "6",
                        10: "m7",
                        11: "maj7",
                    }[interval]
                    tones.append((extension_name, interval))

        expected_score = np.mean([
            frame_scores[i][expected_base]
            for i in indices
        ])
        predicted_score = np.mean([
            frame_scores[i][predicted_base]
            for i in indices
        ])

        evidence = "  ".join(
            f"{label}({NOTE_NAMES[(root + interval) % 12]})="
            f"{normalized[(root + interval) % 12]:.3f}"
            for label, interval in tones
        )

        print(
            f"{start:05.2f}-{end:05.2f}s  "
            f"{expected} -> {predicted_full}"
        )
        print(f"    chroma: {evidence}")
        print(
            f"    mean base score: "
            f"{expected_base}={expected_score:.4f}  "
            f"{predicted_base}={predicted_score:.4f}  "
            f"delta={predicted_score - expected_score:+.4f}"
        )


# ==================================================
# TRANSITION SCORE
# ==================================================

def transition_score(
    previous_chord,
    new_chord,
    templates
):

    # Staying on exactly the same chord
    if previous_chord == new_chord:

        return 0.075

    previous_root = templates[
        previous_chord
    ][
        "root"
    ]

    new_root = templates[
        new_chord
    ][
        "root"
    ]

    # Normal chord change
    score = -0.035

    # Same root, different quality
    if previous_root == new_root:

        minor_types = ("m", "m6", "m7")
        previous_type = previous_chord[len(NOTE_NAMES[previous_root]):]
        new_type = new_chord[len(NOTE_NAMES[new_root]):]
        changes_major_minor_family = (
            (previous_type in minor_types)
            != (new_type in minor_types)
        )

        if changes_major_minor_family:

            return -0.030

        return -0.020

    interval = (
        new_root
        - previous_root
    ) % 12

    # Fifth / fourth motion
    if interval in [
        5,
        7
    ]:

        score += 0.015

    return score


# ==================================================
# VITERBI SEQUENCE DECODING
# ==================================================

def decode_sequence(
    frame_scores,
    frame_pre_quality_scores,
    templates,
    filename=None,
    frame_times=None
):

    chord_names = list(templates.keys())
    roots = list(range(len(NOTE_NAMES)))
    chords_by_root = {
        root: [
            chord for chord in chord_names
            if templates[chord]["root"] == root
        ]
        for root in roots
    }

    def root_emission(frame, root):

        root_name = NOTE_NAMES[root]
        triad_emission = max(
            frame_pre_quality_scores[frame][root_name],
            frame_pre_quality_scores[frame][root_name + "m"]
        )
        extended_emission = max(
            frame_pre_quality_scores[frame][chord]
            for chord in chords_by_root[root]
        )

        return min(
            extended_emission,
            triad_emission + 0.275
        )

    frame_count = len(
        frame_scores
    )

    root_count = len(roots)

    dp = np.full(
        (
            frame_count,
            root_count
        ),
        -np.inf
    )

    backpointer = np.full(
        (
            frame_count,
            root_count
        ),
        -1,
        dtype=int
    )

    # --------------------------
    # First frame
    # --------------------------

    for root in roots:

        dp[
            0,
            root
        ] = root_emission(0, root)

    # --------------------------
    # Dynamic programming
    # --------------------------

    for frame in range(
        1,
        frame_count
    ):

        for new_root in roots:

            emission = root_emission(frame, new_root)

            best_score = -np.inf
            best_previous = -1

            for old_root in roots:

                if old_root == new_root:
                    transition = 0.075
                else:
                    transition = -0.035
                    if (new_root - old_root) % 12 in (5, 7):
                        transition += 0.015

                candidate = (
                    dp[
                        frame - 1,
                        old_root
                    ]
                    + transition
                    + emission
                )

                if candidate > best_score:

                    best_score = candidate
                    best_previous = old_root

            dp[
                frame,
                new_root
            ] = best_score

            backpointer[
                frame,
                new_root
            ] = best_previous

    if (
        filename is not None
        and Path(filename).name == "day1_intro.mp3"
        and frame_times is not None
    ):

        diagnostic_roots = (3, 8)

        print()
        print("Day 1 Viterbi DP diagnostic (17.0-19.0s):")
        print("------------------------------------------")

        for frame, frame_time in enumerate(frame_times):

            if not 17.0 <= frame_time <= 19.0:
                continue

            print(f"{frame_time:.3f}s")

            for root in diagnostic_roots:
                previous_root = backpointer[frame, root]
                previous_name = (
                    "START"
                    if previous_root < 0
                    else NOTE_NAMES[previous_root]
                )
                emission = root_emission(frame, root)

                print(
                    f"    {NOTE_NAMES[root]:<3} "
                    f"emission={emission:+.6f}  "
                    f"dp={dp[frame, root]:+.6f}  "
                    f"previous={previous_name}"
                )

    # --------------------------
    # Backtrack best path
    # --------------------------

    best_index = int(
        np.argmax(
            dp[-1]
        )
    )

    path = [
        best_index
    ]

    for frame in range(
        frame_count - 1,
        0,
        -1
    ):

        best_index = backpointer[
            frame,
            best_index
        ]

        path.append(
            best_index
        )

    path.reverse()

    decoded = []

    for frame, root in enumerate(path):

        candidates = chords_by_root[root]
        root_name = NOTE_NAMES[root]

        if (
            frame_scores[frame][root_name + "m"]
            > frame_scores[frame][root_name]
        ):
            candidates = [
                chord
                for chord in candidates
                if chord != root_name + "maj7"
            ]

        decoded.append(
            max(
                candidates,
                key=frame_scores[frame].get
            )
        )

    return decoded


# ==================================================
# MINIMUM DURATION CLEANUP
# ==================================================

def enforce_minimum_duration(
    decoded,
    frame_scores,
    minimum_frames=4
):
    """
    4 frames x 0.125 seconds = 0.5 seconds.

    Chord segments shorter than this are
    treated as suspicious and merged into
    one of their neighbors.
    """

    result = decoded.copy()

    changed = True

    while changed:

        changed = False

        segments = []

        start = 0

        # --------------------------
        # Find chord segments
        # --------------------------

        for i in range(
            1,
            len(result) + 1
        ):

            if (
                i == len(result)
                or result[i]
                != result[start]
            ):

                segments.append(
                    (
                        start,
                        i,
                        result[start]
                    )
                )

                start = i

        # --------------------------
        # Find short segments
        # --------------------------

        for segment_index, (
            start,
            end,
            chord
        ) in enumerate(
            segments
        ):

            length = (
                end - start
            )

            if length >= minimum_frames:

                continue

            previous_chord = None
            next_chord = None

            if segment_index > 0:

                previous_chord = (
                    segments[
                        segment_index - 1
                    ][2]
                )

            if (
                segment_index
                < len(segments) - 1
            ):

                next_chord = (
                    segments[
                        segment_index + 1
                    ][2]
                )

            # --------------------------
            # Same chord on both sides
            # --------------------------

            if (
                previous_chord is not None
                and previous_chord
                == next_chord
            ):

                replacement = (
                    previous_chord
                )

            # --------------------------
            # Only next neighbor exists
            # --------------------------

            elif previous_chord is None:

                replacement = (
                    next_chord
                )

            # --------------------------
            # Only previous neighbor exists
            # --------------------------

            elif next_chord is None:

                replacement = (
                    previous_chord
                )

            # --------------------------
            # Choose better neighbor
            # --------------------------

            else:

                previous_score = 0.0
                next_score = 0.0

                for frame in range(
                    start,
                    end
                ):

                    previous_score += (
                        frame_scores[
                            frame
                        ][
                            previous_chord
                        ]
                    )

                    next_score += (
                        frame_scores[
                            frame
                        ][
                            next_chord
                        ]
                    )

                if (
                    previous_score
                    >= next_score
                ):

                    replacement = (
                        previous_chord
                    )

                else:

                    replacement = (
                        next_chord
                    )

            # --------------------------
            # Replace short segment
            # --------------------------

            for frame in range(
                start,
                end
            ):

                result[
                    frame
                ] = replacement

            changed = True
            break

    return result


# ==================================================
# EARLY ROOT-CHANGE CORRECTION
# ==================================================

def correct_early_root_changes(
    decoded,
    raw_chords,
    frame_scores,
    templates
):
    """
    Viterbi can occasionally move a chord change
    slightly earlier than the local audio supports.

    If Viterbi changes to a new ROOT, but the raw
    audio still supports the previous root for at
    least two consecutive frames, temporarily keep
    the raw chords in that run.

    Example:

        raw:      F6
        Viterbi:  Dm

    If the previous decoded chord was also rooted on F,
    this prevents the Dm change from occurring too early.
    """

    result = decoded.copy()

    # Apply the same local-evidence check at the beginning
    # of the song, where there is no previous decoded frame.
    initial_decoded_root = templates[
        decoded[0]
    ][
        "root"
    ]
    initial_raw_root = templates[
        raw_chords[0]
    ][
        "root"
    ]

    if initial_raw_root != initial_decoded_root:

        supported_frames = []

        for frame, raw_chord in enumerate(raw_chords):

            if templates[raw_chord]["root"] != initial_raw_root:
                break

            raw_score = frame_scores[frame][raw_chord]
            decoded_score = frame_scores[frame][decoded[frame]]

            if raw_score <= decoded_score + 0.01:
                break

            supported_frames.append(frame)

        if len(supported_frames) >= 3:

            for frame in supported_frames:
                result[frame] = raw_chords[frame]

    i = 1

    while i < len(decoded):

        previous_chord = result[
            i - 1
        ]

        current_chord = decoded[
            i
        ]

        previous_root = templates[
            previous_chord
        ][
            "root"
        ]

        current_root = templates[
            current_chord
        ][
            "root"
        ]

        # No root change occurred
        if current_root == previous_root:

            i += 1
            continue

        supported_frames = []
        frame = i

        while frame < len(decoded):

            raw_chord = raw_chords[
                frame
            ]

            raw_root = templates[
                raw_chord
            ][
                "root"
            ]

            if raw_root != previous_root:

                break

            raw_score = frame_scores[
                frame
            ][
                raw_chord
            ]

            decoded_score = frame_scores[
                frame
            ][
                decoded[
                    frame
                ]
            ]

            if raw_score <= decoded_score + 0.01:

                break

            supported_frames.append(
                frame
            )

            frame += 1

        # Require persistent local evidence across
        # two 0.125-second frames.
        if len(supported_frames) < 2:

            i += 1
            continue

        for frame in supported_frames:

            result[
                frame
            ] = raw_chords[
                frame
            ]

        i = supported_frames[-1] + 1

    return result


# ==================================================
# ANALYZE SONG
# ==================================================

def analyze_song(
    filename
):

    print(
        f"Loading: {filename}"
    )

    # ------------------------------------------------
    # LOAD AUDIO
    # ------------------------------------------------

    y, sr = librosa.load(
        filename,
        mono=True
    )

    # ------------------------------------------------
    # HARMONIC EXTRACTION
    # ------------------------------------------------

    harmonic = (
        librosa.effects.harmonic(
            y=y,
            margin=8
        )
    )

    # ------------------------------------------------
    # FULL-RANGE CHROMA
    # ------------------------------------------------

    chroma = (
        librosa.feature.chroma_cqt(
            y=harmonic,
            sr=sr
        )
    )

    # ------------------------------------------------
    # LOW-RANGE BASS CHROMA
    # ------------------------------------------------

    bass_chroma = (
        librosa.feature.chroma_cqt(
            y=harmonic,
            sr=sr,
            fmin=librosa.note_to_hz(
                "C1"
            ),
            n_octaves=3
        )
    )

    templates = (
        make_chord_templates()
    )

    # ------------------------------------------------
    # KEY DETECTION
    # ------------------------------------------------

    average_song_chroma = (
        np.mean(
            chroma,
            axis=1
        )
    )

    (
        detected_key,
        key_match
    ) = detect_key(
        average_song_chroma
    )

    (
        key_root,
        key_type
    ) = detected_key

    print()

    print(
        "Detected key:",
        NOTE_NAMES[
            key_root
        ],
        key_type
    )

    print(
        f"Key match: "
        f"{key_match:.2f}"
    )

    # ------------------------------------------------
    # FRAME ANALYSIS
    # ------------------------------------------------

    duration = (
        librosa.get_duration(
            y=y,
            sr=sr
        )
    )

    seconds_per_section = (
        0.125
    )

    frame_scores = []
    frame_pre_quality_scores = []
    frame_audio_matches = []
    frame_bass_notes = []
    frame_times = []
    frame_chroma = []

    for start_time in np.arange(
        0,
        duration,
        seconds_per_section
    ):

        end_time = (
            start_time
            + seconds_per_section
        )

        start_frame = (
            librosa.time_to_frames(
                start_time,
                sr=sr
            )
        )

        end_frame = (
            librosa.time_to_frames(
                end_time,
                sr=sr
            )
        )

        section = chroma[
            :,
            start_frame:end_frame
        ]

        bass_section = bass_chroma[
            :,
            start_frame:end_frame
        ]

        if section.shape[1] == 0:

            continue

        average_chroma = np.mean(
            section,
            axis=1
        )

        average_bass = np.mean(
            bass_section,
            axis=1
        )

        (
            scores,
            pre_quality_scores,
            matches,
            bass_note
        ) = score_frame(
            average_chroma,
            average_bass,
            templates,
            key_root,
            key_type
        )

        frame_scores.append(
            scores
        )

        frame_pre_quality_scores.append(
            pre_quality_scores
        )

        frame_audio_matches.append(
            matches
        )

        frame_bass_notes.append(
            bass_note
        )

        frame_times.append(
            start_time
        )

        frame_chroma.append(
            average_chroma
        )

    # ------------------------------------------------
    # RAW CHORDS
    # ------------------------------------------------

    raw_chords = []

    for scores in frame_scores:

        raw_chords.append(
            max(
                scores,
                key=scores.get
            )
        )

    # ------------------------------------------------
    # VITERBI
    # ------------------------------------------------

    decoded = decode_sequence(
        frame_scores,
        frame_pre_quality_scores,
        templates,
        filename=filename,
        frame_times=frame_times
    )

    pre_duration_decoded = (
        decoded.copy()
    )

    # ------------------------------------------------
    # v1.2 MINIMUM DURATION
    # ------------------------------------------------

    decoded = enforce_minimum_duration(
        decoded,
        frame_scores,
        minimum_frames=4
    )

    # ------------------------------------------------
    # NEW EXPERIMENT:
    # EARLY ROOT-CHANGE CORRECTION
    # ------------------------------------------------

    decoded = correct_early_root_changes(
        decoded,
        raw_chords,
        frame_scores,
        templates
    )

    print_day1_quality_diagnostics(
        filename,
        frame_times,
        frame_chroma,
        frame_scores
    )

    # ------------------------------------------------
    # DEBUG SEQUENCE DECISIONS
    # ------------------------------------------------

    debug_times = [
        11.125,
        11.250,
        31.500,
        31.750,
        32.000,
        32.250,
        35.625,
        36.500
    ]

    print()
    print("Sequence decision debug:")
    print("------------------------")

    for debug_time in debug_times:

        closest_index = min(
            range(
                len(frame_times)
            ),
            key=lambda i: abs(
                frame_times[i]
                - debug_time
            )
        )

        raw_chord = raw_chords[
            closest_index
        ]

        viterbi_chord = (
            pre_duration_decoded[
                closest_index
            ]
        )

        final_chord = decoded[
            closest_index
        ]

        print(
            f"{frame_times[closest_index]:.3f}s  "
            f"raw: {raw_chord:<7} "
            f"viterbi: {viterbi_chord:<7} "
            f"final: {final_chord:<7}"
        )

    # ------------------------------------------------
    # DEBUG CHORD SCORES
    # ------------------------------------------------

    print()
    print("Debug chord scores:")
    print("-------------------")

    for debug_time in debug_times:

        closest_index = min(
            range(
                len(frame_times)
            ),
            key=lambda i: abs(
                frame_times[i]
                - debug_time
            )
        )

        scores = frame_scores[
            closest_index
        ]

        best_chords = sorted(
            scores,
            key=scores.get,
            reverse=True
        )[:5]

        bass_note = frame_bass_notes[
            closest_index
        ]

        if bass_note is None:

            bass_name = "?"

        else:

            bass_name = NOTE_NAMES[
                bass_note
            ]

        print()

        print(
            f"{frame_times[closest_index]:.3f}s "
            f"bass: {bass_name}"
        )

        for chord in best_chords:

            print(
                f"    {chord:<7} "
                f"{scores[chord]:.4f}"
            )

    # ------------------------------------------------
    # PRINT DETECTED CHORDS
    # ------------------------------------------------

    print()
    print("Detected chords:")
    print("----------------")

    previous = None

    for i, chord in enumerate(
        decoded
    ):

        if chord == previous:

            continue

        time = frame_times[
            i
        ]

        minutes = int(
            time // 60
        )

        seconds = (
            time % 60
        )

        bass_note = frame_bass_notes[
            i
        ]

        if bass_note is None:

            bass_name = "?"

        else:

            bass_name = NOTE_NAMES[
                bass_note
            ]

        match = (
            frame_audio_matches[
                i
            ][
                chord
            ]
        )

        print(
            f"{minutes}:{seconds:04.1f}  "
            f"{chord:<7} "
            f"match: {match:.2f}  "
            f"bass: {bass_name}"
        )

        previous = chord

    # ------------------------------------------------
    # CHANGE COUNTS
    # ------------------------------------------------

    raw_changes = sum(
        raw_chords[i]
        != raw_chords[i - 1]

        for i in range(
            1,
            len(raw_chords)
        )
    )

    viterbi_changes = sum(
        pre_duration_decoded[i]
        != pre_duration_decoded[
            i - 1
        ]

        for i in range(
            1,
            len(
                pre_duration_decoded
            )
        )
    )

    final_changes = sum(
        decoded[i]
        != decoded[
            i - 1
        ]

        for i in range(
            1,
            len(decoded)
        )
    )

    print()

    print(
        "Sequence cleanup:"
    )

    print(
        f"Raw chord changes: "
        f"{raw_changes}"
    )

    print(
        f"After Viterbi:     "
        f"{viterbi_changes}"
    )

    print(
        f"After duration:    "
        f"{final_changes}"
    )

    # ------------------------------------------------
    # EVALUATION
    # ------------------------------------------------

    try:

        (
            ground_truth,
            evaluation_end
        ) = load_ground_truth(
            ground_truth_path(filename)
        )

        predictions = []

        previous = None

        for i, chord in enumerate(
            decoded
        ):

            if chord != previous:

                predictions.append(
                    (
                        frame_times[i],
                        chord
                    )
                )

                previous = chord

        evaluate(
            ground_truth,
            predictions,
            duration,
            evaluation_end=
                evaluation_end
        )

    except FileNotFoundError:

        print()
        print(
            "No ground-truth annotation found."
        )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage: python "
            "chord_detector.py song.mp3"
        )

        sys.exit()

    analyze_song(
        sys.argv[1]
    )

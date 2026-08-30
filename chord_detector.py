import sys

import librosa
import numpy as np

from evaluate import (
    load_ground_truth,
    evaluate
)


NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
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

        if (
            relative_root in [0, 5]
            and chord_type in [
                "",
                "6",
                "maj7"
            ]
        ):
            return 0.04

        if (
            relative_root == 7
            and chord_type in [
                "",
                "7"
            ]
        ):
            return 0.04

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

        if (
            relative_root in [0, 5, 7]
            and chord_type in [
                "m",
                "m6",
                "m7"
            ]
        ):
            return 0.04

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
# BASS
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

    audio_match = cosine_similarity(
        chroma,
        template
    )

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

    bass_bonus = 0.0

    if bass_note is not None:

        if bass_note == root:

            bass_bonus += (
                0.12
                * bass_strength
            )

        elif template[
            bass_note
        ] == 1:

            bass_bonus += (
                0.025
                * bass_strength
            )

    key_bonus = chord_key_bonus(
        root,
        chord_type,
        key_root,
        key_type
    )

    extension_penalty = 0.0

    if chord_type in [
        "6",
        "m6",
        "7",
        "maj7",
        "m7"
    ]:

        extension_penalty = 0.035

    final_score = (
        audio_match
        + bass_bonus
        + key_bonus
        - unexplained_penalty
        - extension_penalty
    )

    return (
        final_score,
        audio_match
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
    audio_matches = {}

    for (
        chord_name,
        chord_info
    ) in templates.items():

        (
            score,
            audio_match
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

        audio_matches[
            chord_name
        ] = audio_match

    return (
        scores,
        audio_matches,
        bass_note
    )


# ==================================================
# TRANSITION SCORE
# ==================================================

def transition_score(
    previous_chord,
    new_chord,
    templates
):

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

    score = -0.035

    if previous_root == new_root:

        return -0.020

    interval = (
        new_root
        - previous_root
    ) % 12

    if interval in [
        5,
        7
    ]:

        score += 0.015

    return score


# ==================================================
# VITERBI
# ==================================================

def decode_sequence(
    frame_scores,
    templates
):

    chord_names = list(
        templates.keys()
    )

    frame_count = len(
        frame_scores
    )

    chord_count = len(
        chord_names
    )

    dp = np.full(
        (
            frame_count,
            chord_count
        ),
        -np.inf
    )

    backpointer = np.full(
        (
            frame_count,
            chord_count
        ),
        -1,
        dtype=int
    )

    for i, chord in enumerate(
        chord_names
    ):

        dp[
            0,
            i
        ] = frame_scores[
            0
        ][
            chord
        ]

    for frame in range(
        1,
        frame_count
    ):

        for new_index, new_chord in enumerate(
            chord_names
        ):

            emission = frame_scores[
                frame
            ][
                new_chord
            ]

            best_score = -np.inf
            best_previous = -1

            for old_index, old_chord in enumerate(
                chord_names
            ):

                candidate = (
                    dp[
                        frame - 1,
                        old_index
                    ]
                    + transition_score(
                        old_chord,
                        new_chord,
                        templates
                    )
                    + emission
                )

                if candidate > best_score:

                    best_score = candidate
                    best_previous = old_index

            dp[
                frame,
                new_index
            ] = best_score

            backpointer[
                frame,
                new_index
            ] = best_previous

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

    return [
        chord_names[index]
        for index in path
    ]


# ==================================================
# MINIMUM DURATION CLEANUP
# ==================================================

def enforce_minimum_duration(
    decoded,
    frame_scores,
    minimum_frames=4
):
    """
    4 frames x 0.125 sec = 0.5 seconds.

    Short chord segments are treated as
    suspicious and merged into a neighbor.
    """

    result = decoded.copy()

    changed = True

    while changed:

        changed = False

        segments = []

        start = 0

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
            # Only one neighbor
            # --------------------------

            elif previous_chord is None:

                replacement = next_chord

            elif next_chord is None:

                replacement = previous_chord

            # --------------------------
            # Choose whichever neighbor
            # fits the short segment better
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
# ANALYZE
# ==================================================

def analyze_song(
    filename
):

    print(
        f"Loading: {filename}"
    )

    y, sr = librosa.load(
        filename,
        mono=True
    )

    harmonic = (
        librosa.effects.harmonic(
            y=y,
            margin=8
        )
    )

    chroma = (
        librosa.feature.chroma_cqt(
            y=harmonic,
            sr=sr
        )
    )

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
    # KEY
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
    # FRAMES
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
    frame_audio_matches = []
    frame_bass_notes = []
    frame_times = []

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

        frame_audio_matches.append(
            matches
        )

        frame_bass_notes.append(
            bass_note
        )

        frame_times.append(
            start_time
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
        templates
    )

    pre_duration_decoded = (
        decoded.copy()
    )

    # ------------------------------------------------
    # NEW v1.2 MINIMUM DURATION
    # ------------------------------------------------

    decoded = enforce_minimum_duration(
        decoded,
        frame_scores,
        minimum_frames=4
    )

    # ------------------------------------------------
    # PRINT CHORDS
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

        time = frame_times[i]

        minutes = int(
            time // 60
        )

        seconds = (
            time % 60
        )

        bass_note = (
            frame_bass_notes[i]
        )

        if bass_note is None:

            bass_name = "?"

        else:

            bass_name = (
                NOTE_NAMES[
                    bass_note
                ]
            )

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
        != pre_duration_decoded[i - 1]

        for i in range(
            1,
            len(
                pre_duration_decoded
            )
        )
    )

    final_changes = sum(
        decoded[i]
        != decoded[i - 1]

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
            "ground_truth.txt"
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
            "No ground_truth.txt found."
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
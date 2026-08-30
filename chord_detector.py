import sys

import librosa
import numpy as np


NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


CHORD_TYPES = {
    "": [0, 4, 7],          # major
    "m": [0, 3, 7],         # minor
    "6": [0, 4, 7, 9],      # major 6
    "m6": [0, 3, 7, 9],     # minor 6
    "7": [0, 4, 7, 10],     # dominant 7
    "maj7": [0, 4, 7, 11],  # major 7
    "m7": [0, 3, 7, 10],    # minor 7
}


MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]


# ==================================================
# CHORD TEMPLATES
# ==================================================

def make_chord_templates():

    templates = {}

    for root in range(12):

        for chord_type, intervals in CHORD_TYPES.items():

            template = np.zeros(12)

            for interval in intervals:

                note = (
                    root + interval
                ) % 12

                template[note] = 1

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

def detect_key(
    chroma
):

    best_key = None
    best_score = -1

    for root in range(12):

        # Major
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

        # Minor
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
# KEY CONTEXT
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

        # I, IV, V
        if (
            relative_root in [0, 5, 7]
            and chord_type in [
                "",
                "6",
                "maj7"
            ]
        ):
            return 0.04

        # ii, iii, vi
        if (
            relative_root in [2, 4, 9]
            and chord_type in [
                "m",
                "m6",
                "m7"
            ]
        ):
            return 0.04

        # V7
        if (
            relative_root == 7
            and chord_type == "7"
        ):
            return 0.05

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

    # ------------------------------------------
    # AUDIO MATCH
    # ------------------------------------------

    audio_match = cosine_similarity(
        chroma,
        template
    )

    # ------------------------------------------
    # EXTRA / UNEXPLAINED NOTES
    # ------------------------------------------

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
        unexplained * 0.16
    )

    # ------------------------------------------
    # BASS SUPPORT
    # ------------------------------------------

    bass_bonus = 0.0

    if bass_note is not None:

        if bass_note == root:

            bass_bonus = (
                0.12
                * bass_strength
            )

        elif template[
            bass_note
        ] == 1:

            # Possible inversion
            bass_bonus = (
                0.025
                * bass_strength
            )

    # ------------------------------------------
    # KEY
    # ------------------------------------------

    key_bonus = chord_key_bonus(
        root,
        chord_type,
        key_root,
        key_type
    )

    # ------------------------------------------
    # EXTENSIONS NEED EXTRA EVIDENCE
    # ------------------------------------------

    extension_penalty = 0.0

    if chord_type in [
        "6",
        "m6",
        "7",
        "maj7",
        "m7"
    ]:

        extension_penalty = 0.035

    # ------------------------------------------
    # FINAL EMISSION SCORE
    # ------------------------------------------

    score = (
        audio_match
        + bass_bonus
        + key_bonus
        - unexplained_penalty
        - extension_penalty
    )

    return (
        score,
        audio_match
    )


# ==================================================
# SCORE EVERY CHORD FOR ONE FRAME
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
# CHORD RELATIONSHIPS
# ==================================================

def chord_root(
    chord_name,
    templates
):

    return templates[
        chord_name
    ][
        "root"
    ]


def chord_type(
    chord_name,
    templates
):

    return templates[
        chord_name
    ][
        "type"
    ]


def base_quality(
    chord_name,
    templates
):

    chord_info = templates[
        chord_name
    ]

    chord_type_name = chord_info[
        "type"
    ]

    if chord_type_name in [
        "m",
        "m6",
        "m7"
    ]:

        return "minor"

    return "major"


# ==================================================
# TRANSITION COST
# ==================================================

def transition_score(
    previous_chord,
    new_chord,
    templates
):

    # Staying on the same chord is strongly preferred
    if previous_chord == new_chord:

        return 0.075

    previous_root = chord_root(
        previous_chord,
        templates
    )

    new_root = chord_root(
        new_chord,
        templates
    )

    previous_type = chord_type(
        previous_chord,
        templates
    )

    new_type = chord_type(
        new_chord,
        templates
    )

    previous_quality = base_quality(
        previous_chord,
        templates
    )

    new_quality = base_quality(
        new_chord,
        templates
    )

    score = -0.035

    # ------------------------------------------
    # Same root but changing extension
    #
    # C -> Cmaj7
    # Am -> Am7
    # ------------------------------------------

    if previous_root == new_root:

        score = -0.015

        # Extension changes should still need
        # some evidence.
        if (
            previous_type
            != new_type
        ):
            score -= 0.01

        return score

    # ------------------------------------------
    # Common musical root motions
    # ------------------------------------------

    interval = (
        new_root - previous_root
    ) % 12

    # Perfect fourth / fifth movement
    if interval in [
        5,
        7
    ]:
        score += 0.015

    # Stepwise root motion
    if interval in [
        2,
        10
    ]:
        score += 0.005

    # Relative major/minor-like motion
    if interval in [
        3,
        9
    ]:

        if (
            previous_quality
            != new_quality
        ):

            score += 0.01

    return score


# ==================================================
# VITERBI / SEQUENCE DECODING
# ==================================================

def decode_sequence(
    frame_scores,
    templates
):

    chord_names = list(
        templates.keys()
    )

    number_of_frames = len(
        frame_scores
    )

    number_of_chords = len(
        chord_names
    )

    if number_of_frames == 0:
        return []

    # dp[t, c]
    #
    # best total score ending on chord c
    # at frame t

    dp = np.full(
        (
            number_of_frames,
            number_of_chords
        ),
        -np.inf
    )

    backpointer = np.full(
        (
            number_of_frames,
            number_of_chords
        ),
        -1,
        dtype=int
    )

    # ------------------------------------------
    # FIRST FRAME
    # ------------------------------------------

    for chord_index, chord in enumerate(
        chord_names
    ):

        dp[
            0,
            chord_index
        ] = frame_scores[
            0
        ][
            chord
        ]

    # ------------------------------------------
    # ALL FOLLOWING FRAMES
    # ------------------------------------------

    for frame_index in range(
        1,
        number_of_frames
    ):

        for new_index, new_chord in enumerate(
            chord_names
        ):

            emission = frame_scores[
                frame_index
            ][
                new_chord
            ]

            best_previous_score = -np.inf
            best_previous_index = -1

            for (
                previous_index,
                previous_chord
            ) in enumerate(
                chord_names
            ):

                transition = transition_score(
                    previous_chord,
                    new_chord,
                    templates
                )

                candidate = (
                    dp[
                        frame_index - 1,
                        previous_index
                    ]
                    + transition
                    + emission
                )

                if (
                    candidate
                    > best_previous_score
                ):

                    best_previous_score = (
                        candidate
                    )

                    best_previous_index = (
                        previous_index
                    )

            dp[
                frame_index,
                new_index
            ] = best_previous_score

            backpointer[
                frame_index,
                new_index
            ] = best_previous_index

    # ------------------------------------------
    # TRACE BACK BEST PATH
    # ------------------------------------------

    best_final_index = int(
        np.argmax(
            dp[
                -1
            ]
        )
    )

    path_indices = [
        best_final_index
    ]

    for frame_index in range(
        number_of_frames - 1,
        0,
        -1
    ):

        previous_index = (
            backpointer[
                frame_index,
                path_indices[-1]
            ]
        )

        path_indices.append(
            previous_index
        )

    path_indices.reverse()

    decoded = [
        chord_names[
            index
        ]
        for index in path_indices
    ]

    return decoded


# ==================================================
# REMOVE VERY SHORT FINAL CHORDS
# ==================================================

def clean_decoded_sequence(
    decoded
):

    if len(
        decoded
    ) < 3:

        return decoded

    cleaned = decoded.copy()

    # One frame = 0.125 sec
    #
    # Replace isolated one-frame chord:
    #
    # C C F6 C C
    #
    # becomes
    #
    # C C C C C

    for i in range(
        1,
        len(decoded) - 1
    ):

        if (
            decoded[
                i - 1
            ]
            == decoded[
                i + 1
            ]
            and decoded[
                i
            ]
            != decoded[
                i - 1
            ]
        ):

            cleaned[
                i
            ] = decoded[
                i - 1
            ]

    return cleaned


# ==================================================
# MAIN
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

    # ------------------------------------------
    # HARMONIC AUDIO
    # ------------------------------------------

    harmonic = (
        librosa.effects.harmonic(
            y=y,
            margin=8
        )
    )

    # ------------------------------------------
    # FULL CHROMA
    # ------------------------------------------

    chroma = (
        librosa.feature.chroma_cqt(
            y=harmonic,
            sr=sr
        )
    )

    # ------------------------------------------
    # BASS CHROMA
    # ------------------------------------------

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

    # ==========================================
    # KEY
    # ==========================================

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

    # ==========================================
    # FRAME ANALYSIS
    # ==========================================

    duration = (
        librosa.get_duration(
            y=y,
            sr=sr
        )
    )

    seconds_per_section = 0.125

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

        if (
            section.shape[1]
            == 0
        ):
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
            audio_matches,
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
            audio_matches
        )

        frame_bass_notes.append(
            bass_note
        )

        frame_times.append(
            start_time
        )

    # ==========================================
    # RAW RESULTS
    # ==========================================

    raw_chords = []

    for scores in frame_scores:

        raw_chord = max(
            scores,
            key=scores.get
        )

        raw_chords.append(
            raw_chord
        )

    # ==========================================
    # SEQUENCE DECODING
    # ==========================================

    decoded = decode_sequence(
        frame_scores,
        templates
    )

    decoded = clean_decoded_sequence(
        decoded
    )

    # ==========================================
    # OUTPUT
    # ==========================================

    print()

    print(
        "Detected chords:"
    )

    print(
        "----------------"
    )

    previous_chord = None

    for i, chord in enumerate(
        decoded
    ):

        if (
            chord
            == previous_chord
        ):
            continue

        start_time = frame_times[
            i
        ]

        minutes = int(
            start_time // 60
        )

        seconds = (
            start_time % 60
        )

        bass_note = (
            frame_bass_notes[
                i
            ]
        )

        if bass_note is None:

            bass_name = "?"

        else:

            bass_name = (
                NOTE_NAMES[
                    bass_note
                ]
            )

        audio_match = (
            frame_audio_matches[
                i
            ][
                chord
            ]
        )

        print(
            f"{minutes}:{seconds:04.1f}  "
            f"{chord:<7} "
            f"match: {audio_match:.2f}  "
            f"bass: {bass_name}"
        )

        previous_chord = chord

    # ==========================================
    # DEBUG SUMMARY
    # ==========================================

    raw_changes = 0
    final_changes = 0

    for i in range(
        1,
        len(raw_chords)
    ):

        if (
            raw_chords[i]
            != raw_chords[
                i - 1
            ]
        ):
            raw_changes += 1

    for i in range(
        1,
        len(decoded)
    ):

        if (
            decoded[i]
            != decoded[
                i - 1
            ]
        ):
            final_changes += 1

    print()

    print(
        "Sequence cleanup:"
    )

    print(
        f"Raw chord changes: "
        f"{raw_changes}"
    )

    print(
        f"Final chord changes: "
        f"{final_changes}"
    )


# ==================================================
# START PROGRAM
# ==================================================

if __name__ == "__main__":

    if len(
        sys.argv
    ) < 2:

        print(
            "Usage: python "
            "chord_detector.py song.mp3"
        )

        sys.exit()

    analyze_song(
        sys.argv[1]
    )
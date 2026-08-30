def load_ground_truth(filename):
    """
    Read entries like:

    0.0,C
    1.8,G
    3.5,Am
    """

    truth = []

    with open(filename, "r") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            time_text, chord = line.split(",")

            truth.append(
                (
                    float(time_text),
                    chord.strip()
                )
            )

    return truth


def base_chord(chord):
    """
    Remove chord extensions while preserving
    major/minor quality.

    Cmaj7 -> C
    C7    -> C
    C6    -> C

    Am7   -> Am
    Am6   -> Am
    """

    if chord.endswith("maj7"):
        return chord[:-4]

    if chord.endswith("m7"):
        return chord[:-1]

    if chord.endswith("m6"):
        return chord[:-1]

    if chord.endswith("7"):
        return chord[:-1]

    if chord.endswith("6"):
        return chord[:-1]

    return chord


def root_note(chord):
    """
    Strip everything except the root.

    Cmaj7 -> C
    Am7   -> A
    F6    -> F
    """

    base = base_chord(chord)

    if base.endswith("m"):
        return base[:-1]

    return base


def chord_at_time(events, time):
    """
    Find the chord active at a particular time.
    """

    current_chord = events[0][1]

    for event_time, chord in events:

        if event_time > time:
            break

        current_chord = chord

    return current_chord


def near_boundary(
    ground_truth,
    time,
    tolerance
):
    """
    Return True when a sample is very close
    to an annotated chord change.

    We don't score those frames because the
    exact transition timestamp is approximate.
    """

    # Skip the first event because 0.0 is
    # simply the beginning of the recording.
    for event_time, chord in ground_truth[1:]:

        if abs(
            time - event_time
        ) <= tolerance:

            return True

    return False


def evaluate(
    ground_truth,
    predictions,
    duration,
    step=0.125,
    boundary_tolerance=0.30
):

    total = 0

    exact_correct = 0
    base_correct = 0
    root_correct = 0

    skipped = 0
    mistakes = []

    time = 0.0

    while time < duration:

        # Don't judge frames right next to
        # a chord-change boundary.
        if near_boundary(
            ground_truth,
            time,
            boundary_tolerance
        ):

            skipped += 1
            time += step
            continue

        expected = chord_at_time(
            ground_truth,
            time
        )

        predicted = chord_at_time(
            predictions,
            time
        )

        total += 1

        if predicted == expected:
            exact_correct += 1

        if (
            base_chord(predicted)
            == base_chord(expected)
        ):
            base_correct += 1

        if (
            root_note(predicted)
            == root_note(expected)
        ):
            root_correct += 1

        if (
            base_chord(predicted)
            != base_chord(expected)
        ):

            mistakes.append(
                (
                    time,
                    expected,
                    predicted
                )
            )

        time += step

    if total == 0:

        print(
            "No frames available "
            "for evaluation."
        )

        return

    exact_accuracy = (
        exact_correct
        / total
        * 100
    )

    base_accuracy = (
        base_correct
        / total
        * 100
    )

    root_accuracy = (
        root_correct
        / total
        * 100
    )

    print()
    print("Evaluation")
    print("----------")

    print(
        f"Root accuracy:        "
        f"{root_accuracy:.1f}%"
    )

    print(
        f"Base chord accuracy:  "
        f"{base_accuracy:.1f}%"
    )

    print(
        f"Exact chord accuracy: "
        f"{exact_accuracy:.1f}%"
    )

    print()

    print(
        f"Evaluated frames: "
        f"{total}"
    )

    print(
        f"Boundary frames skipped: "
        f"{skipped}"
    )

    print(
        f"Incorrect base frames: "
        f"{len(mistakes)}"
    )

    print()

    print(
        "First 15 real mistakes:"
    )

    for (
        time,
        expected,
        predicted
    ) in mistakes[:15]:

        print(
            f"{time:05.2f}s  "
            f"expected: {expected:<5} "
            f"got: {predicted}"
        )
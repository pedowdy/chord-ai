# Local experiment workflow

The working tree is the retained baseline. Trials never modify it unless a patch
passes the acceptance gate and `--accept` is explicitly supplied.

1. Refresh the baseline after an intentional retained change:
   `.venv/bin/python experiment_loop.py init`
2. Put one small proposed change in a patch file.
3. Run it in a disposable directory:
   `.venv/bin/python experiment_loop.py trial --name "short name" --hypothesis "one testable claim" --patch experiments/proposal.patch`
4. Review the logged result. Re-run with `--accept` only when the verdict is
   `KEEP` and the change is genuinely justified.

The default gate requires at least one improvement among the five songs' root,
base, and exact accuracies, with no regression in any of those 15 measurements.
Every completed trial is appended to `log.md`, including rejected trials.

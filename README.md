# Escape Thalamus Task

Pacman-like flight initiation distance task for Thalamus. Subjects control a
token along a horizontal reward track, collect disappearing dots, and retreat to
the right-side safe zone before a fast red or slow yellow predator catches them.

## Run

Launch the task controller with the helper script:

```bash
cd /Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape
./run_escape.sh
```

The helper uses:

- Thalamus source: `/Users/kamrenkhan/Desktop/Research/RESTORE/Project/Thalamus/source`
- Python venv: `/Users/kamrenkhan/Desktop/Research/RESTORE/Project/venv-thalamus`
- Python pipeline mode: `-y`, because a source checkout does not include the compiled `thalamus/native` executable.

If you later use a Thalamus install that includes the native executable:

```bash
ESCAPE_USE_NATIVE=1 ./run_escape.sh
```

Manual equivalent:

```bash
cd /Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape
PYTHONPATH=/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape:/Users/kamrenkhan/Desktop/Research/RESTORE/Project/Thalamus/source \
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/venv-thalamus/bin/python \
-m thalamus.task_controller -y --ext escape_thalamus_ext
```

In the Task Controller UI, add `Escape FID (Predator)` to a task cluster and set
the run goal to the desired number of trials.

For step-by-step GUI instructions, see `docs/gui_run.md`.

## Controls

- Hold left arrow to move toward the predator and collect reward dots.
- Hold right arrow to retreat to the safe zone.

## Defaults

The default attack distances follow the recent SEEG FID implementation:

- Fast predator: attack distance sampled from mean 60, SD 3.
- Slow predator: attack distance sampled from mean 10, SD 3.

These distances are represented on a 100-unit abstract axis and scaled to the
current display size.

## Data

Each launch creates a new local session folder:

```text
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape/data/<SESSION_ID>/
```

The launcher prints the session ID and data directory at startup. The task writes:

- `summary.txt`: number of trials, accuracy, total reward, session duration, average trial duration, and risk-aversiveness scores.
- `trials.jsonl`: one JSON trial summary per trial.
- `trials.tsv`: tabular trial summary.
- `frames.jsonl`: sampled frame-level token/predator positions.
- `success_reward_by_condition.png`: success and reward by fast vs slow predator.
- `escape_points_by_condition.png`: flight initiation distance distribution with empirical attack-distance mean and SD.
- `distance_time_by_trial.png`: predator-token distance over trial time.
- `x_axis_escape_and_attack.png`: retreat, chase initiation, and distance profiles over the token x-axis.

The same trial and frame-level records are also written to the Thalamus text stream:

- `escape_trial_start`
- `escape_reward`
- `escape_attack`
- `escape_frame`
- `escape_trial`

Risk-aversiveness is reported two ways: raw FID normalized to the 100-unit axis,
and condition-adjusted risk, `(flight initiation distance - sampled attack distance) / 100`.
Higher values indicate earlier retreat at larger predator-prey distance.

See `docs/protocol.md` and `configs/escape_defaults.json` for the current design
and configurable defaults.

## Quick Check

With Thalamus available on the Python path:

```bash
PYTHONPATH=/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape:/Users/kamrenkhan/Desktop/Research/RESTORE/Project/Thalamus/source \
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/venv-thalamus/bin/python \
-m escape_thalamus_ext._smoke_test_escape
```

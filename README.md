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

Manual equivalent:

```bash
cd /Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape
PYTHONPATH=/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape:/Users/kamrenkhan/Desktop/Research/RESTORE/Project/Thalamus/source \
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/venv-thalamus/bin/python \
-m thalamus.task_controller --ext escape_thalamus_ext
```

In the Task Controller UI, add `Escape FID (Predator)` to a task cluster and set
the run goal to the desired number of trials.

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

Trial and frame-level logs are JSON records on the Thalamus text stream:

- `escape_trial_start`
- `escape_reward`
- `escape_attack`
- `escape_frame`
- `escape_trial`

See `docs/protocol.md` and `configs/escape_defaults.json` for the current design
and configurable defaults.

## Quick Check

With Thalamus available on the Python path:

```bash
PYTHONPATH=/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape:/Users/kamrenkhan/Desktop/Research/RESTORE/Project/Thalamus/source \
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/venv-thalamus/bin/python \
-m escape_thalamus_ext._smoke_test_escape
```

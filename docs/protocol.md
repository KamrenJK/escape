# Escape FID Task Protocol

## Trial Structure

Each trial samples one active predator condition:

- `fast`: red predator, longer attack distance, faster attack acceleration.
- `slow`: yellow predator, shorter attack distance, slower attack acceleration.

The subject starts in the right-side safe zone and controls a blue token with the
left and right arrow keys. Reward dots are arranged evenly across a horizontal
track. Dots disappear immediately when collected. The trial succeeds when the
subject has collected at least one token and returns to the safe zone before
capture. If the predator catches the subject before safe-zone return, the trial
ends in failure and the trial tokens are lost.

## Attack Logic

The task uses a 100-unit abstract horizontal axis. Predator attack onset is
sampled as a prey-predator distance threshold:

- fast predator: Gaussian mean 60 units, SD 3 units.
- slow predator: Gaussian mean 10 units, SD 3 units.

Before attack onset, the predator approaches slowly. At attack onset, it
accelerates toward the subject, with condition-specific acceleration and maximum
speed parameters.

## Feedback

Success feedback shows a green plus and the number of tokens gained. Failure
feedback shows a red X and "failure".

The task no longer shows a predator-condition screen before each trial.

## Logging

The task writes JSON logs to the Thalamus text stream:

- `escape_trial_start`: trial index, predator condition, attack threshold, safe
  zone boundary, and dot count.
- `escape_reward`: one event per collected dot.
- `escape_attack`: attack onset timing and distance.
- `escape_frame`: sampled frame-level position state.
- `escape_trial`: final outcome and trial summary.

Each launcher run also creates `data/<SESSION_ID>/` with raw JSONL/TSV outputs,
summary text, and PNG plots. Risk-aversiveness is defined as earlier retreat at a
larger predator-prey distance. The condition-adjusted score is:

```text
(flight initiation distance - sampled attack distance) / 100
```

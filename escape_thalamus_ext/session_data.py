from __future__ import annotations

import csv
import json
import math
import os
import pathlib
import statistics
import time
import typing


PREDATORS = ("fast", "slow")


def get_session_dir() -> pathlib.Path:
    session_dir = os.environ.get("ESCAPE_SESSION_DIR")
    if session_dir:
        path = pathlib.Path(session_dir)
    else:
        session_id = os.environ.get("ESCAPE_SESSION_ID") or time.strftime("%Y%m%d_%H%M%S")
        path = pathlib.Path.cwd() / "data" / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_jsonl(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def append_frame(payload: dict) -> None:
    append_jsonl(get_session_dir() / "frames.jsonl", payload)


def append_trial(payload: dict) -> None:
    session_dir = get_session_dir()
    append_jsonl(session_dir / "trials.jsonl", payload)
    _write_trials_tsv(session_dir, _load_jsonl(session_dir / "trials.jsonl"))
    write_summary_and_plots(session_dir)


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    result = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                result.append(json.loads(line))
    return result


def _write_trials_tsv(session_dir: pathlib.Path, trials: list[dict]) -> None:
    if not trials:
        return
    columns = [
        "trial_index",
        "predator",
        "success",
        "outcome",
        "tokens",
        "trial_duration_s",
        "attack_distance_units",
        "attack_on_elapsed_s",
        "attack_on_token_units",
        "attack_on_predator_units",
        "escape_on_elapsed_s",
        "escape_token_units",
        "escape_predator_units",
        "flight_initiation_distance_units",
        "condition_adjusted_risk",
        "final_token_units",
        "final_predator_units",
    ]
    with (session_dir / "trials.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for trial in trials:
            writer.writerow(trial)


def _finite(values: typing.Iterable[typing.Any]) -> list[float]:
    result = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result.append(number)
    return result


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else math.nan


def _std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0 if values else math.nan


def _by_predator(records: list[dict]) -> dict[str, list[dict]]:
    return {predator: [r for r in records if r.get("predator") == predator] for predator in PREDATORS}


def _score_summary(trials: list[dict]) -> tuple[float, float]:
    fids = _finite(t.get("flight_initiation_distance_units") for t in trials)
    margins = _finite(t.get("condition_adjusted_risk") for t in trials)
    risk_raw = _mean([value / 100.0 for value in fids])
    risk_adjusted = _mean(margins)
    return risk_raw, risk_adjusted


def _summary_text(trials: list[dict]) -> str:
    n_trials = len(trials)
    successes = [bool(t.get("success")) for t in trials]
    accuracy = sum(successes) / n_trials if n_trials else math.nan
    total_reward = sum(int(t.get("tokens") or 0) for t in trials if t.get("success"))
    durations = _finite(t.get("trial_duration_s") for t in trials)
    started = _finite(t.get("trial_start_wall_time") for t in trials)
    ended = _finite(t.get("trial_end_wall_time") for t in trials)
    duration = (max(ended) - min(started)) if started and ended else math.nan
    average_trial_duration = _mean(durations)
    risk_raw, risk_adjusted = _score_summary(trials)

    lines = [
        "Escape FID session summary",
        f"number_of_trials\t{n_trials}",
        f"accuracy\t{accuracy:.6f}" if math.isfinite(accuracy) else "accuracy\tnan",
        f"total_reward\t{total_reward}",
        f"duration_s\t{duration:.6f}" if math.isfinite(duration) else "duration_s\tnan",
        (
            f"average_trial_duration_s\t{average_trial_duration:.6f}"
            if math.isfinite(average_trial_duration)
            else "average_trial_duration_s\tnan"
        ),
        (
            f"risk_aversiveness_raw_fid_0_to_1\t{risk_raw:.6f}"
            if math.isfinite(risk_raw)
            else "risk_aversiveness_raw_fid_0_to_1\tnan"
        ),
        (
            f"risk_aversiveness_condition_adjusted\t{risk_adjusted:.6f}"
            if math.isfinite(risk_adjusted)
            else "risk_aversiveness_condition_adjusted\tnan"
        ),
        "",
        "Risk score note: higher values mean earlier retreat at a larger predator-prey distance. "
        "The condition-adjusted score is (flight initiation distance - sampled attack distance) / 100.",
    ]
    return "\n".join(lines) + "\n"


def _condition_stats(trials: list[dict], key: str) -> dict[str, tuple[float, float]]:
    grouped = _by_predator(trials)
    return {
        predator: (
            _mean(_finite(record.get(key) for record in records)),
            _std(_finite(record.get(key) for record in records)),
        )
        for predator, records in grouped.items()
    }


def write_summary_and_plots(session_dir: pathlib.Path) -> None:
    trials = _load_jsonl(session_dir / "trials.jsonl")
    frames = _load_jsonl(session_dir / "frames.jsonl")
    (session_dir / "summary.txt").write_text(_summary_text(trials), encoding="utf-8")
    if trials:
        _plot_success_reward(session_dir, trials)
        _plot_escape_points(session_dir, trials)
        _plot_distance(session_dir, frames)
        _plot_x_axis(session_dir, trials, frames)


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _colors() -> dict[str, str]:
    return {"fast": "#d64b4b", "slow": "#4fb7ad"}


def _legend_if_any(ax) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if handles and labels:
        ax.legend()


def _plot_success_reward(session_dir: pathlib.Path, trials: list[dict]) -> None:
    plt = _setup_matplotlib()
    colors = _colors()
    grouped = _by_predator(trials)
    labels = ["Fast", "Slow"]
    predators = list(PREDATORS)
    success = []
    reward = []
    for predator in predators:
        records = grouped[predator]
        success.append(sum(bool(r.get("success")) for r in records) / len(records) if records else 0.0)
        reward.append(_mean([float(r.get("tokens") or 0) for r in records if r.get("success")]))

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    axes[0].bar(labels, [value * 100 for value in success], color=[colors[p] for p in predators], alpha=0.35)
    for predator, label in zip(predators, labels):
        y = [100 if r.get("success") else 0 for r in grouped[predator]]
        axes[0].scatter([label] * len(y), y, c=colors[predator], alpha=0.75)
    axes[0].set_ylabel("% escape")
    axes[0].set_ylim(0, 105)
    axes[0].set_title("Trial Success")

    axes[1].bar(labels, reward, color=[colors[p] for p in predators], alpha=0.35)
    for predator, label in zip(predators, labels):
        y = [float(r.get("tokens") or 0) for r in grouped[predator] if r.get("success")]
        axes[1].scatter([label] * len(y), y, c=colors[predator], alpha=0.75)
    axes[1].set_ylabel("Tokens retained")
    axes[1].set_title("Reward")
    fig.savefig(session_dir / "success_reward_by_condition.png", dpi=160)
    plt.close(fig)


def _plot_escape_points(session_dir: pathlib.Path, trials: list[dict]) -> None:
    plt = _setup_matplotlib()
    colors = _colors()
    attack_stats = _condition_stats(trials, "attack_distance_units")
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    for predator in PREDATORS:
        values = _finite(t.get("flight_initiation_distance_units") for t in trials if t.get("predator") == predator)
        if values:
            ax.hist(values, bins=min(12, max(4, len(values))), density=True, alpha=0.25, color=colors[predator], label=f"{predator} FID")
        mean_attack, std_attack = attack_stats[predator]
        if math.isfinite(mean_attack):
            ax.axvline(mean_attack, color=colors[predator], linestyle="--", linewidth=2, label=f"{predator} attack mean")
            ax.axvspan(mean_attack - std_attack, mean_attack + std_attack, color=colors[predator], alpha=0.12)
    ax.set_xlabel("Flight initiation distance: predator-prey distance at retreat")
    ax.set_ylabel("Density")
    ax.set_title("Escape Point Distribution")
    _legend_if_any(ax)
    fig.savefig(session_dir / "escape_points_by_condition.png", dpi=160)
    plt.close(fig)


def _plot_distance(session_dir: pathlib.Path, frames: list[dict]) -> None:
    if not frames:
        return
    plt = _setup_matplotlib()
    colors = _colors()
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    for trial_index in sorted(set(int(f["trial_index"]) for f in frames)):
        trial_frames = [f for f in frames if int(f["trial_index"]) == trial_index]
        if not trial_frames:
            continue
        predator = str(trial_frames[0].get("predator"))
        ax.plot(
            [float(f["elapsed_s"]) for f in trial_frames],
            [float(f["distance_units"]) for f in trial_frames],
            color=colors.get(predator, "#777777"),
            alpha=0.25,
            linewidth=1,
        )
    ax.axhline(0, color="#333333", linewidth=1, linestyle=":")
    ax.set_xlabel("Trial time (s)")
    ax.set_ylabel("Token - predator distance (axis units)")
    ax.set_title("Predator-Token Distance Across Trials")
    fig.savefig(session_dir / "distance_time_by_trial.png", dpi=160)
    plt.close(fig)


def _plot_x_axis(session_dir: pathlib.Path, trials: list[dict], frames: list[dict]) -> None:
    plt = _setup_matplotlib()
    colors = _colors()
    fig, axes = plt.subplots(3, 1, figsize=(8, 9), constrained_layout=True)
    attack_stats = _condition_stats(trials, "attack_on_token_units")
    for predator in PREDATORS:
        records = [t for t in trials if t.get("predator") == predator]
        escape_x = _finite(t.get("escape_token_units") for t in records)
        attack_x = _finite(t.get("attack_on_token_units") for t in records)
        if escape_x:
            axes[0].hist(escape_x, bins=min(12, max(4, len(escape_x))), alpha=0.30, color=colors[predator], label=f"{predator} retreat x")
        if attack_x:
            axes[1].hist(attack_x, bins=min(12, max(4, len(attack_x))), alpha=0.30, color=colors[predator], label=f"{predator} attack x")
        mean_attack, std_attack = attack_stats[predator]
        if math.isfinite(mean_attack):
            for ax in axes:
                ax.axvline(mean_attack, color=colors[predator], linestyle="--", linewidth=2)
                ax.axvspan(mean_attack - std_attack, mean_attack + std_attack, color=colors[predator], alpha=0.12)

        predator_frames = [f for f in frames if f.get("predator") == predator]
        if predator_frames:
            bins = [i * 10.0 for i in range(11)]
            centers = [(bins[i] + bins[i + 1]) / 2.0 for i in range(len(bins) - 1)]
            means = []
            for low, high in zip(bins[:-1], bins[1:]):
                values = [
                    float(f["distance_units"])
                    for f in predator_frames
                    if low <= float(f.get("token_units", math.nan)) < high
                ]
                means.append(_mean(values))
            axes[2].plot(centers, means, color=colors[predator], marker="o", label=f"{predator} mean distance")

    axes[0].set_title("Retreat/Escape Decisions By Token X Position")
    axes[0].set_xlabel("Token x-axis position (0 = predator side, 100 = safe side)")
    axes[0].set_ylabel("Count")
    _legend_if_any(axes[0])
    axes[1].set_title("Empirical Attacker Chase Initiation By Token X Position")
    axes[1].set_xlabel("Token x-axis position at chase initiation")
    axes[1].set_ylabel("Count")
    _legend_if_any(axes[1])
    axes[2].set_title("Predator-Token Distance By Token X Position")
    axes[2].set_xlabel("Token x-axis position")
    axes[2].set_ylabel("Mean token - predator distance")
    _legend_if_any(axes[2])
    fig.savefig(session_dir / "x_axis_escape_and_attack.png", dpi=160)
    plt.close(fig)

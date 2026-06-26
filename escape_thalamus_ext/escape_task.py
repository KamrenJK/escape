"""
Pacman-like flight initiation distance task for Thalamus.

One trial has one active predator condition. The subject controls a token on a
horizontal track with the left and right arrow keys, collects reward dots, then
retreats to the right-side safe zone before capture.
"""

from __future__ import annotations

import datetime
import json
import math
import random
import time
import typing

from thalamus.config import ObservableCollection
from thalamus.qt import QColor, QFont, QPointF, QRect, QRectF, Qt, QWidget, QVBoxLayout
from thalamus.task_controller.util import TaskResult, animate
from thalamus.task_controller.widgets import Form
from PyQt6.QtCore import QEvent, QObject

try:
    from thalamus import task_controller_pb2
except Exception:  # pragma: no cover - present in Thalamus runtime
    task_controller_pb2 = None


AXIS_UNITS = 100.0
FAST = "fast"
SLOW = "slow"


class Config(typing.NamedTuple):
    predator_order: str
    fast_probability: float
    dot_count: int
    token_speed_units_s: float
    pre_attack_speed_units_s: float
    fast_attack_accel_units_s2: float
    slow_attack_accel_units_s2: float
    fast_attack_max_speed_units_s: float
    slow_attack_max_speed_units_s: float
    fast_attack_mean_units: float
    fast_attack_sd_units: float
    slow_attack_mean_units: float
    slow_attack_sd_units: float
    safe_zone_units: float
    collision_radius_units: float
    ready_s: float
    feedback_s: float
    max_trial_s: float
    frame_hz: float
    frame_log_hz: float
    log_frames: bool
    allow_zero_token_success: bool


def create_widget(task_config: ObservableCollection) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout()
    widget.setLayout(layout)

    form = Form.build(
        task_config,
        ["Name:", "Value:"],
        Form.String("Predator order (random | alternate | fast | slow)", "predator_order", "random"),
        Form.Constant("Fast probability", "fast_probability", 0.5, precision=2),
        Form.Constant("Reward dots", "dot_count", 17, precision=0),
        Form.Constant("Token speed", "token_speed_units_s", 35.0, " units/s", precision=1),
        Form.Constant("Predator approach speed", "pre_attack_speed_units_s", 6.0, " units/s", precision=1),
        Form.Constant("Fast attack acceleration", "fast_attack_accel_units_s2", 95.0, " units/s2", precision=1),
        Form.Constant("Slow attack acceleration", "slow_attack_accel_units_s2", 35.0, " units/s2", precision=1),
        Form.Constant("Fast attack max speed", "fast_attack_max_speed_units_s", 70.0, " units/s", precision=1),
        Form.Constant("Slow attack max speed", "slow_attack_max_speed_units_s", 30.0, " units/s", precision=1),
        Form.Constant("Fast attack mean distance", "fast_attack_mean_units", 60.0, " units", precision=1),
        Form.Constant("Fast attack SD", "fast_attack_sd_units", 3.0, " units", precision=1),
        Form.Constant("Slow attack mean distance", "slow_attack_mean_units", 10.0, " units", precision=1),
        Form.Constant("Slow attack SD", "slow_attack_sd_units", 3.0, " units", precision=1),
        Form.Constant("Safe zone width", "safe_zone_units", 8.0, " units", precision=1),
        Form.Constant("Collision radius", "collision_radius_units", 3.0, " units", precision=1),
        Form.Constant("Ready screen", "ready_s", 0.8, " s", precision=2),
        Form.Constant("Feedback screen", "feedback_s", 1.25, " s", precision=2),
        Form.Constant("Max trial time", "max_trial_s", 20.0, " s", precision=1),
        Form.Constant("Frame rate", "frame_hz", 60.0, " Hz", precision=1),
        Form.Constant("Frame log rate", "frame_log_hz", 60.0, " Hz", precision=1),
        Form.Bool("Log frames", "log_frames", True),
        Form.Bool("Allow zero-token success", "allow_zero_token_success", False),
    )
    layout.addWidget(form)
    return widget


def _read_cfg(task_config: ObservableCollection) -> Config:
    return Config(
        predator_order=str(task_config.get("predator_order", "random")).lower(),
        fast_probability=float(task_config.get("fast_probability", 0.5)),
        dot_count=max(1, int(task_config.get("dot_count", 17))),
        token_speed_units_s=float(task_config.get("token_speed_units_s", 35.0)),
        pre_attack_speed_units_s=float(task_config.get("pre_attack_speed_units_s", 6.0)),
        fast_attack_accel_units_s2=float(task_config.get("fast_attack_accel_units_s2", 95.0)),
        slow_attack_accel_units_s2=float(task_config.get("slow_attack_accel_units_s2", 35.0)),
        fast_attack_max_speed_units_s=float(task_config.get("fast_attack_max_speed_units_s", 70.0)),
        slow_attack_max_speed_units_s=float(task_config.get("slow_attack_max_speed_units_s", 30.0)),
        fast_attack_mean_units=float(task_config.get("fast_attack_mean_units", 60.0)),
        fast_attack_sd_units=max(0.0, float(task_config.get("fast_attack_sd_units", 3.0))),
        slow_attack_mean_units=float(task_config.get("slow_attack_mean_units", 10.0)),
        slow_attack_sd_units=max(0.0, float(task_config.get("slow_attack_sd_units", 3.0))),
        safe_zone_units=float(task_config.get("safe_zone_units", 8.0)),
        collision_radius_units=float(task_config.get("collision_radius_units", 3.0)),
        ready_s=float(task_config.get("ready_s", 0.8)),
        feedback_s=float(task_config.get("feedback_s", 1.25)),
        max_trial_s=float(task_config.get("max_trial_s", 20.0)),
        frame_hz=max(1.0, float(task_config.get("frame_hz", 60.0))),
        frame_log_hz=max(0.0, float(task_config.get("frame_log_hz", 60.0))),
        log_frames=bool(task_config.get("log_frames", True)),
        allow_zero_token_success=bool(task_config.get("allow_zero_token_success", False)),
    )


def _choose_predator(task_config: ObservableCollection, cfg: Config) -> str:
    order = cfg.predator_order
    if order in (FAST, SLOW):
        return order
    if order == "alternate":
        last = str(task_config.get("_last_predator", SLOW))
        predator = FAST if last == SLOW else SLOW
    else:
        predator = FAST if random.random() < cfg.fast_probability else SLOW
    task_config["_last_predator"] = predator
    return predator


def _sample_attack_distance(predator: str, cfg: Config) -> float:
    if predator == FAST:
        value = random.gauss(cfg.fast_attack_mean_units, cfg.fast_attack_sd_units)
    else:
        value = random.gauss(cfg.slow_attack_mean_units, cfg.slow_attack_sd_units)
    return max(0.0, min(AXIS_UNITS, value))


def _predator_color(predator: str) -> QColor:
    if predator == FAST:
        return QColor(230, 36, 36)
    return QColor(232, 196, 39)


def _to_screen_x(unit_x: float, widget: QWidget, left: float, width: float) -> float:
    return left + (unit_x / AXIS_UNITS) * width


def _track_geometry(widget: QWidget) -> typing.Tuple[float, float, float]:
    width = max(1.0, widget.width() * 0.82)
    left = (widget.width() - width) / 2.0
    y = widget.height() * 0.55
    return left, width, y


def _draw_centered_text(painter, widget: QWidget, text: str, color: QColor, size: int) -> None:
    painter.setPen(color)
    painter.setFont(QFont("Arial", size))
    painter.drawText(
        QRect(0, 0, widget.width(), widget.height()),
        int(Qt.AlignmentFlag.AlignCenter),
        text,
    )


def _make_ready_renderer(widget: QWidget, predator: str):
    def renderer(painter) -> None:
        painter.fillRect(QRect(0, 0, widget.width(), widget.height()), QColor(10, 10, 12))
        color = _predator_color(predator)
        label = "FAST" if predator == FAST else "SLOW"
        _draw_centered_text(painter, widget, label, color, 72)

    return renderer


def _make_feedback_renderer(widget: QWidget, success: bool, tokens: int):
    def renderer(painter) -> None:
        painter.fillRect(QRect(0, 0, widget.width(), widget.height()), QColor(10, 10, 12))
        if success:
            _draw_centered_text(painter, widget, f"+\n{tokens} tokens gained", QColor(60, 220, 105), 58)
        else:
            _draw_centered_text(painter, widget, "X\nfailure", QColor(230, 36, 36), 64)

    return renderer


def _make_game_renderer(widget: QWidget, state: "TrialState"):
    def renderer(painter) -> None:
        painter.fillRect(QRect(0, 0, widget.width(), widget.height()), QColor(10, 10, 12))
        left, width, y = _track_geometry(widget)
        safe_start = AXIS_UNITS - state.safe_zone_units
        safe_x = _to_screen_x(safe_start, widget, left, width)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(28, 38, 48))
        painter.drawRect(QRectF(safe_x, y - 56, left + width - safe_x, 112))

        painter.setPen(QColor(150, 154, 162))
        painter.drawLine(int(left), int(y), int(left + width), int(y))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(245, 238, 180))
        for index, dot_x in enumerate(state.dot_units):
            if index in state.collected_dot_indices:
                continue
            sx = _to_screen_x(dot_x, widget, left, width)
            painter.drawEllipse(QPointF(sx, y), 5.0, 5.0)

        predator_x = _to_screen_x(state.predator_units, widget, left, width)
        token_x = _to_screen_x(state.token_units, widget, left, width)

        painter.setBrush(_predator_color(state.predator))
        radius = 16.0 if not state.attack_started else 22.0
        painter.drawEllipse(QPointF(predator_x, y), radius, radius)

        painter.setBrush(QColor(80, 170, 255))
        painter.drawEllipse(QPointF(token_x, y), 14.0, 14.0)

        painter.setPen(QColor(225, 225, 225))
        painter.setFont(QFont("Arial", 22))
        painter.drawText(QRect(0, 20, widget.width(), 34), int(Qt.AlignmentFlag.AlignCenter), str(state.tokens))

    return renderer


class TrialState:
    def __init__(self, predator: str, cfg: Config):
        self.predator = predator
        self.safe_zone_units = max(1.0, min(30.0, cfg.safe_zone_units))
        self.safe_start_units = AXIS_UNITS - self.safe_zone_units
        self.token_units = AXIS_UNITS - self.safe_zone_units / 2.0
        self.predator_units = 0.0
        self.predator_speed_units_s = cfg.pre_attack_speed_units_s
        self.attack_distance_units = _sample_attack_distance(predator, cfg)
        self.attack_started = False
        self.attack_on_perf: typing.Optional[float] = None
        self.attack_on_elapsed_s: typing.Optional[float] = None
        self.tokens = 0
        self.has_left_safe_zone = False
        self.collected_dot_indices: set[int] = set()
        spacing = AXIS_UNITS / float(cfg.dot_count + 2)
        self.dot_units = [spacing * float(i + 1) for i in range(cfg.dot_count)]

    def in_safe_zone(self) -> bool:
        return self.token_units >= self.safe_start_units


class _KeyStateTracker(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.down_keys: set[int] = set()

    def is_down(self, key: int) -> bool:
        return int(key) in self.down_keys

    def eventFilter(self, _obj, event) -> bool:  # type: ignore[override]
        try:
            event_type = event.type()
            key = int(event.key())
            is_auto_repeat = bool(event.isAutoRepeat())
        except Exception:
            return False

        if is_auto_repeat:
            return False
        if event_type == QEvent.Type.KeyPress:
            self.down_keys.add(key)
        elif event_type == QEvent.Type.KeyRelease:
            self.down_keys.discard(key)
        return False


def _focus_widget(widget: QWidget) -> None:
    try:
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        widget.setFocus(Qt.FocusReason.OtherFocusReason)
        window = widget.window()
        if window is not None:
            window.activateWindow()
            window.raise_()
    except Exception:
        return


async def _publish_state(context, state: str) -> None:
    servicer = getattr(context, "servicer", None)
    if servicer is None or task_controller_pb2 is None:
        return
    try:
        await servicer.publish_state(task_controller_pb2.BehavState(state=state))
    except Exception:
        return


def _set_handler(widget, name: str, handler) -> None:
    try:
        setattr(widget, name, handler)
    except Exception:
        return


def _frame_payload(trial_index: int, state: TrialState, elapsed_s: float, outcome: typing.Optional[str]) -> dict:
    return {
        "trial_index": trial_index,
        "elapsed_s": elapsed_s,
        "predator": state.predator,
        "token_units": state.token_units,
        "predator_units": state.predator_units,
        "distance_units": state.token_units - state.predator_units,
        "attack_distance_units": state.attack_distance_units,
        "attack_started": state.attack_started,
        "tokens": state.tokens,
        "in_safe_zone": state.in_safe_zone(),
        "outcome": outcome,
    }


@animate(60)
async def run(context) -> TaskResult:
    assert context.widget is not None, "Escape task requires a canvas"
    cfg = _read_cfg(context.task_config)

    trial_index = int(context.task_config.get("trial_index", 0))
    predator = _choose_predator(context.task_config, cfg)
    state = TrialState(predator, cfg)
    key_tracker = _KeyStateTracker()
    context.widget.installEventFilter(key_tracker)
    _focus_widget(context.widget)
    outcome: typing.Optional[str] = None
    success = False

    context.widget.renderer = _make_ready_renderer(context.widget, predator)
    context.widget.update()
    await _publish_state(context, "escape_ready")
    await context.log(
        json.dumps(
            {
                "escape_trial_start": {
                    "trial_index": trial_index,
                    "predator": predator,
                    "attack_distance_units": state.attack_distance_units,
                    "safe_start_units": state.safe_start_units,
                    "dot_count": len(state.dot_units),
                }
            }
        )
    )
    await context.sleep(datetime.timedelta(seconds=cfg.ready_s))

    left_key = Qt.Key.Key_Left
    right_key = Qt.Key.Key_Right

    def key_release_handler(_event) -> None:
        context.process()

    _set_handler(context.widget, "key_release_handler", key_release_handler)
    context.widget.renderer = _make_game_renderer(context.widget, state)
    context.widget.update()
    await _publish_state(context, "escape_active")

    start_perf = time.perf_counter()
    last_perf = start_perf
    last_frame_log_perf = start_perf
    frame_interval_s = 1.0 / cfg.frame_hz
    frame_log_interval_s = 1.0 / cfg.frame_log_hz if cfg.frame_log_hz > 0 else math.inf
    attack_logged = False

    while outcome is None:
        now = time.perf_counter()
        elapsed_s = now - start_perf
        dt = max(0.0, min(0.1, now - last_perf))
        last_perf = now

        direction = 0.0
        if key_tracker.is_down(left_key):
            direction -= 1.0
        if key_tracker.is_down(right_key):
            direction += 1.0
        state.token_units = max(0.0, min(AXIS_UNITS, state.token_units + direction * cfg.token_speed_units_s * dt))
        if not state.in_safe_zone():
            state.has_left_safe_zone = True

        for index, dot_x in enumerate(state.dot_units):
            if index in state.collected_dot_indices:
                continue
            if abs(state.token_units - dot_x) <= cfg.collision_radius_units:
                state.collected_dot_indices.add(index)
                state.tokens += 1
                await context.log(
                    json.dumps(
                        {
                            "escape_reward": {
                                "trial_index": trial_index,
                                "elapsed_s": elapsed_s,
                                "dot_index": index,
                                "dot_units": dot_x,
                                "tokens": state.tokens,
                            }
                        }
                    )
                )

        distance = state.token_units - state.predator_units
        if not state.attack_started and state.has_left_safe_zone and distance <= state.attack_distance_units:
            state.attack_started = True
            state.attack_on_perf = now
            state.attack_on_elapsed_s = elapsed_s

        if state.attack_started:
            accel = cfg.fast_attack_accel_units_s2 if predator == FAST else cfg.slow_attack_accel_units_s2
            max_speed = cfg.fast_attack_max_speed_units_s if predator == FAST else cfg.slow_attack_max_speed_units_s
            state.predator_speed_units_s = min(max_speed, state.predator_speed_units_s + accel * dt)
            if not attack_logged:
                attack_logged = True
                await _publish_state(context, "escape_attack")
                await context.log(
                    json.dumps(
                        {
                            "escape_attack": {
                                "trial_index": trial_index,
                                "elapsed_s": elapsed_s,
                                "predator": predator,
                                "distance_units": distance,
                                "attack_distance_units": state.attack_distance_units,
                            }
                        }
                    )
                )

        if state.has_left_safe_zone:
            state.predator_units = min(AXIS_UNITS, state.predator_units + state.predator_speed_units_s * dt)

        if state.has_left_safe_zone and state.in_safe_zone() and (state.tokens > 0 or cfg.allow_zero_token_success):
            outcome = "success"
            success = True
        elif state.has_left_safe_zone and not state.in_safe_zone() and state.predator_units >= state.token_units - cfg.collision_radius_units:
            outcome = "caught"
        elif elapsed_s >= cfg.max_trial_s:
            outcome = "timeout"

        if cfg.log_frames and now - last_frame_log_perf >= frame_log_interval_s:
            last_frame_log_perf = now
            await context.log(json.dumps({"escape_frame": _frame_payload(trial_index, state, elapsed_s, outcome)}))

        context.widget.update()
        await context.sleep(datetime.timedelta(seconds=frame_interval_s))

    _set_handler(context.widget, "key_release_handler", lambda _event: None)
    context.widget.removeEventFilter(key_tracker)

    await _publish_state(context, f"escape_{outcome}")
    trial_result = {
        "trial_index": trial_index,
        "predator": predator,
        "success": success,
        "outcome": outcome,
        "tokens": state.tokens,
        "collected_dot_indices": sorted(state.collected_dot_indices),
        "attack_distance_units": state.attack_distance_units,
        "attack_on_elapsed_s": state.attack_on_elapsed_s,
        "final_token_units": state.token_units,
        "final_predator_units": state.predator_units,
    }
    context.behav_result = trial_result
    await context.log(json.dumps({"escape_trial": trial_result}))
    context.task_config["trial_index"] = trial_index + 1

    context.widget.renderer = _make_feedback_renderer(context.widget, success, state.tokens)
    context.widget.update()
    await context.sleep(datetime.timedelta(seconds=cfg.feedback_s))

    return TaskResult(success)

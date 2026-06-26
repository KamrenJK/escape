import asyncio
import json

from thalamus.config import ObservableDict
from thalamus.qt import QApplication, Qt
from PyQt6.QtCore import QEvent

from . import escape_task


class _Servicer:
    async def publish_state(self, _msg):
        return None


class _KeyEvent:
    def __init__(self, key, event_type):
        self._key = key
        self._event_type = event_type

    def key(self):
        return self._key

    def type(self):
        return self._event_type

    def isAutoRepeat(self):
        return False


class _Widget:
    def __init__(self):
        self.key_press_handler = lambda _e: None
        self.key_release_handler = lambda _e: None
        self.renderer = lambda _p: None
        self._event_filters = []

    def width(self):
        return 1000

    def height(self):
        return 700

    def update(self):
        return None

    def installEventFilter(self, event_filter):
        self._event_filters.append(event_filter)
        return None

    def removeEventFilter(self, event_filter):
        if event_filter in self._event_filters:
            self._event_filters.remove(event_filter)
        return None

    def dispatch_key(self, key, event_type):
        event = _KeyEvent(key, event_type)
        for event_filter in list(self._event_filters):
            event_filter.eventFilter(self, event)
        if event_type == QEvent.Type.KeyRelease:
            self.key_release_handler(event)

    def setFocusPolicy(self, _policy):
        return None

    def setFocus(self, _reason):
        return None

    def window(self):
        return None


class _Ctx:
    def __init__(self, task_config):
        self.task_config = task_config
        self.widget = _Widget()
        self.servicer = _Servicer()
        self.behav_result = {}
        self._log = []
        self._started_press = False
        self._started_retreat = False
        self._start_time = None

    async def sleep(self, duration):
        if self._start_time is None:
            self._start_time = asyncio.get_event_loop().time()
        elapsed = asyncio.get_event_loop().time() - self._start_time
        if not self._started_press and elapsed >= 0.03:
            self._started_press = True
            self.widget.dispatch_key(Qt.Key.Key_Left, QEvent.Type.KeyPress)
        if not self._started_retreat and elapsed >= 0.85:
            self._started_retreat = True
            self.widget.dispatch_key(Qt.Key.Key_Left, QEvent.Type.KeyRelease)
            self.widget.dispatch_key(Qt.Key.Key_Right, QEvent.Type.KeyPress)
        await asyncio.sleep(min(max(duration.total_seconds(), 0.0), 0.02))

    def until(self, condition):
        async def inner():
            while not condition():
                await asyncio.sleep(0)

        return asyncio.get_event_loop().create_task(inner())

    def any(self, *awaitables):
        async def inner():
            done, _ = await asyncio.wait(
                [asyncio.ensure_future(f) for f in awaitables],
                return_when=asyncio.FIRST_COMPLETED,
            )
            return await next(iter(done))

        return asyncio.get_event_loop().create_task(inner())

    def process(self):
        return None

    async def log(self, text: str):
        self._log.append(text)


async def _main():
    _app = QApplication.instance() or QApplication([])
    cfg = ObservableDict(
        {
            "predator_order": "slow",
            "dot_count": 5,
            "ready_s": 0.0,
            "feedback_s": 0.0,
            "max_trial_s": 5.0,
            "frame_hz": 60.0,
            "frame_log_hz": 60.0,
            "token_speed_units_s": 80.0,
            "pre_attack_speed_units_s": 1.0,
            "slow_attack_accel_units_s2": 5.0,
            "slow_attack_max_speed_units_s": 12.0,
            "slow_attack_mean_units": 1.0,
            "slow_attack_sd_units": 0.0,
            "log_frames": True,
        }
    )
    ctx = _Ctx(cfg)
    result = await escape_task.run(ctx)
    assert result.success
    assert callable(ctx.widget.key_release_handler)
    assert ctx.behav_result["tokens"] >= 1
    assert ctx.behav_result["outcome"] == "success"
    decoded = [json.loads(item) for item in ctx._log]
    trials = [item["escape_trial"] for item in decoded if "escape_trial" in item]
    frames = [item["escape_frame"] for item in decoded if "escape_frame" in item]
    assert len(trials) == 1
    assert frames


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()

import typing

from thalamus.task_controller.task_context import TaskDescription

from . import escape_task


def tasks() -> typing.List[TaskDescription]:
    return [
        TaskDescription(
            "escape_fid",
            "Escape FID (Predator)",
            escape_task.create_widget,
            escape_task.run,
        ),
    ]


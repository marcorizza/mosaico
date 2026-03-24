import logging
from contextlib import nullcontext
from threading import Lock

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

LOGGER = logging.getLogger(__name__)


class SequenceProgress:
    def __init__(self, console: Console) -> None:
        self.console = console
        self.enabled = console.is_terminal
        self._lock = Lock()
        self.progress = Progress(
            TextColumn("[bold cyan]{task.fields[name]}"),
            BarColumn(),
            MofNCompleteColumn(),
            "[progress.percentage]{task.percentage:>5.1f}%",
            "•",
            TimeRemainingColumn(),
            "•",
            TimeElapsedColumn(),
            console=console,
            expand=True,
            disable=not self.enabled,
        )
        self.topic_tasks: dict[str, TaskID] = {}
        self.global_task: TaskID | None = None

    def setup(self, topic_totals: dict[str, int]) -> None:
        total_messages = sum(topic_totals.values())
        for topic_name, total in topic_totals.items():
            self.topic_tasks[topic_name] = self.progress.add_task(
                "",
                total=max(total, 1),
                name=topic_name,
            )

        self.global_task = self.progress.add_task(
            "",
            total=max(total_messages, 1),
            name="Total Upload",
        )

    def live(self):
        if not self.enabled:
            return nullcontext()
        return Live(self.progress, console=self.console, refresh_per_second=10)

    def update_status(self, topic_name: str, status: str, style: str = "white") -> None:
        task_id = self.topic_tasks.get(topic_name)
        if task_id is None:
            return

        with self._lock:
            self.progress.update(task_id, name=f"[{style}]{topic_name}: {status}")

    def advance(self, topic_name: str) -> None:
        task_id = self.topic_tasks.get(topic_name)
        with self._lock:
            if task_id is not None:
                self._advance_task(task_id)

            if self.global_task is not None:
                self._advance_task(self.global_task)

    def complete_topic(self, topic_name: str) -> None:
        task_id = self.topic_tasks.get(topic_name)
        if task_id is None:
            return

        with self._lock:
            task = self.progress.tasks[task_id]
            if task.total is not None:
                self.progress.update(task_id, completed=task.total)

    def complete_all(self) -> None:
        if self.global_task is None:
            return

        with self._lock:
            task = self.progress.tasks[self.global_task]
            if task.total is not None:
                self.progress.update(self.global_task, completed=task.total)

    def _advance_task(self, task_id: TaskID) -> None:
        task = self.progress.tasks[task_id]

        if task.total is not None and task.completed >= task.total:
            self.progress.update(task_id, total=task.total + 1)

        self.progress.advance(task_id)
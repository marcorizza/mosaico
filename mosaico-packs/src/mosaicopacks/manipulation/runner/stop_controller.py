from __future__ import annotations

import logging
import signal
from types import FrameType

LOGGER = logging.getLogger(__name__)


class StopController:
    def __init__(self) -> None:
        self._interrupt_count = 0
        self._stop_requested = False
        self._previous_handler = None

    def __call__(self) -> bool:
        return self._stop_requested

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested

    def request_stop(self) -> None:
        self._stop_requested = True

    def install(self) -> None:
        self._previous_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def restore(self) -> None:
        if self._previous_handler is None:
            return

        signal.signal(signal.SIGINT, self._previous_handler)
        self._previous_handler = None

    def _handle_sigint(self, _signum: int, _frame: FrameType | None) -> None:
        self._interrupt_count += 1
        self._stop_requested = True

        if self._interrupt_count == 1:
            LOGGER.warning(
                "Ctrl-C received. Stopping after the current operation and printing a final recap."
            )
            raise KeyboardInterrupt

        LOGGER.error("Second Ctrl-C received. Exiting immediately.")
        raise SystemExit(130)

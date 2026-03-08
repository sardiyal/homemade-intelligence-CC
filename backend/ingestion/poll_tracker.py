"""In-memory tracker for RSS poll status."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic


@dataclass
class PollResult:
    source_name: str
    new_articles: int
    polled_at: datetime


@dataclass
class PollStatus:
    last_poll_started: datetime | None = None
    last_poll_completed: datetime | None = None
    last_poll_duration_seconds: float | None = None
    is_polling: bool = False
    results: list[PollResult] = field(default_factory=list)
    total_polls: int = 0
    next_scheduled_poll: datetime | None = None


_status = PollStatus()
_poll_start_mono: float | None = None


def mark_poll_start() -> None:
    global _poll_start_mono
    _status.is_polling = True
    _status.last_poll_started = datetime.now(UTC)
    _poll_start_mono = monotonic()


def mark_poll_complete(results: dict[str, int]) -> None:
    global _poll_start_mono
    now = datetime.now(UTC)
    _status.is_polling = False
    _status.last_poll_completed = now
    _status.total_polls += 1

    if _poll_start_mono is not None:
        _status.last_poll_duration_seconds = round(monotonic() - _poll_start_mono, 2)
        _poll_start_mono = None

    _status.results = [
        PollResult(source_name=name, new_articles=count, polled_at=now) for name, count in results.items()
    ]


def set_next_scheduled_poll(next_run: datetime | None) -> None:
    _status.next_scheduled_poll = next_run


def get_poll_status() -> PollStatus:
    return _status

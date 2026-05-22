"""Suggest API poll windows from the local WC schedule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.tournament import Fixture, load_fixtures

# 90 min + half-time + stoppage buffer before we expect FT in API.
MINUTES_AFTER_KICKOFF = 135
SESSION_GAP_HOURS = 4


@dataclass(frozen=True)
class PollWindow:
    day: str
    poll_at: datetime
    match_numbers: tuple[int, ...]
    last_kickoff: datetime


def _kickoff_sessions(fixtures: list[Fixture]) -> dict[str, list[list[Fixture]]]:
    by_day: dict[str, list[Fixture]] = {}
    for fixture in fixtures:
        day = fixture.kickoff_at.date().isoformat()
        by_day.setdefault(day, []).append(fixture)

    sessions_by_day: dict[str, list[list[Fixture]]] = {}
    for day, day_fixtures in sorted(by_day.items()):
        ordered = sorted(day_fixtures, key=lambda fixture: fixture.kickoff_at)
        sessions: list[list[Fixture]] = []
        current: list[Fixture] = []

        for fixture in ordered:
            if not current:
                current = [fixture]
                continue

            gap = fixture.kickoff_at - current[-1].kickoff_at
            if gap <= timedelta(hours=SESSION_GAP_HOURS):
                current.append(fixture)
            else:
                sessions.append(current)
                current = [fixture]

        if current:
            sessions.append(current)

        sessions_by_day[day] = sessions

    return sessions_by_day


def poll_windows(
    *,
    now: datetime | None = None,
    only_future: bool = True,
) -> list[PollWindow]:
    now = now or datetime.now(timezone.utc)
    windows: list[PollWindow] = []

    for day, sessions in _kickoff_sessions(load_fixtures()).items():
        for session in sessions:
            last_kickoff = session[-1].kickoff_at
            poll_at = last_kickoff + timedelta(minutes=MINUTES_AFTER_KICKOFF)
            if only_future and poll_at <= now:
                continue

            windows.append(
                PollWindow(
                    day=day,
                    poll_at=poll_at,
                    match_numbers=tuple(fixture.match_number for fixture in session),
                    last_kickoff=last_kickoff,
                )
            )

    return sorted(windows, key=lambda window: window.poll_at)


def estimate_daily_requests(windows: list[PollWindow]) -> dict[str, int]:
    """Rough API calls per day: one batched /fixtures?ids= call per poll window."""
    counts: dict[str, int] = {}
    for window in windows:
        counts[window.day] = counts.get(window.day, 0) + 1
    return counts

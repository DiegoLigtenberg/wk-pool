"""Print suggested daily API poll times based on the local WC schedule."""

from __future__ import annotations

from datetime import datetime, timezone

from app.poll_schedule import MINUTES_AFTER_KICKOFF, estimate_daily_requests, poll_windows


def main() -> int:
    now = datetime.now(timezone.utc)
    windows = poll_windows(now=now, only_future=False)
    future = poll_windows(now=now, only_future=True)

    print(f"Poll windows (kickoff + {MINUTES_AFTER_KICKOFF} min), grouped by match sessions:\n")
    for window in windows:
        marker = "upcoming" if window in future else "past"
        kickoffs = ", ".join(str(number) for number in window.match_numbers)
        print(
            f"{window.day}  poll {window.poll_at.strftime('%H:%M')} UTC  "
            f"matches [{kickoffs}]  ({marker})"
        )

    daily = estimate_daily_requests(future)
    if daily:
        print("\nEstimated API calls per day (1 batched /fixtures?ids= per poll):")
        for day, count in sorted(daily.items()):
            print(f"  {day}: {count} call(s)")

    busiest = max(daily.values()) if daily else 0
    print(
        f"\nWith 100 requests/day on the free plan you have plenty of headroom "
        f"(busiest upcoming day ~ {busiest} poll call(s), plus occasional remap)."
    )
    print(
        "\nRecommended: run `poetry run python scripts/sync_football_results.py` "
        "at each poll time (cron / Railway scheduled job), 2–4× on busy match days."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

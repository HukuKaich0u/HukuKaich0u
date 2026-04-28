#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib import error, request


GRAPHQL_URL = "https://api.github.com/graphql"
CURRENT_STREAK_RE = re.compile(r"Current streak \d+ days?")
BEST_STREAK_RE = re.compile(r"Best streak \d+ days?")


def compute_streak(days: list[dict[str, object]]) -> dict[str, int]:
    current = 0
    maximum = 0

    for day in days:
        contribution_count = int(day["contributionCount"])
        if contribution_count > 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0

    return {"current": current, "max": maximum}


def sync_streak_labels(svg_text: str, current_streak: int, max_streak: int) -> str:
    updated = CURRENT_STREAK_RE.sub(f"Current streak {current_streak} days", svg_text, count=1)
    updated = BEST_STREAK_RE.sub(f"Best streak {max_streak} days", updated, count=1)
    return updated


def build_contribution_query(login: str, start_iso: str, end_iso: str) -> str:
    return f"""
query {{
  user(login: "{login}") {{
    calendar: contributionsCollection(from: "{start_iso}", to: "{end_iso}") {{
      contributionCalendar {{
        weeks {{
          contributionDays {{
            contributionCount
            date
          }}
        }}
      }}
    }}
  }}
}}
""".strip()


def fetch_contribution_days(token: str, login: str, now: datetime | None = None) -> list[dict[str, object]]:
    if now is None:
        now = datetime.now(timezone.utc)

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = start.replace(year=start.year - 1)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999000)

    payload = json.dumps({"query": build_contribution_query(login, start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z"))}).encode("utf-8")
    req = request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "sync-metrics-streaks",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"GitHub GraphQL request failed with status {exc.code}") from exc

    if "errors" in body:
        raise RuntimeError(f"GitHub GraphQL errors: {body['errors']}")

    weeks = body["data"]["user"]["calendar"]["contributionCalendar"]["weeks"]
    return [day for week in weeks for day in week["contributionDays"]]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: sync_metrics_streaks.py <svg-path>", file=sys.stderr)
        return 1

    token = os.environ.get("METRICS_TOKEN")
    if not token:
        raise RuntimeError("METRICS_TOKEN is required")
    login = os.environ.get("GITHUB_REPOSITORY_OWNER", "HukuKaich0u")

    svg_path = Path(argv[1])
    svg_text = svg_path.read_text(encoding="utf-8")
    streak = compute_streak(fetch_contribution_days(token=token, login=login))
    updated_svg = sync_streak_labels(svg_text, current_streak=streak["current"], max_streak=streak["max"])

    if updated_svg != svg_text:
        svg_path.write_text(updated_svg, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

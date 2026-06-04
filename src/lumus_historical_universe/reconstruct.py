from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = ROOT / "data/processed/membership_changes.csv"
QUALITY_PATH = ROOT / "artifacts/reconstruction_quality.csv"


@dataclass
class MembershipResult:
    date: str
    members: list[str]
    quality_flag: str
    warning: str = ""


def load_changes(path: Path = PROCESSED_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def coverage_bounds(changes: list[dict[str, str]] | None = None) -> tuple[str | None, str | None]:
    rows = changes if changes is not None else load_changes()
    dates = sorted(row["effective_date"] for row in rows if row.get("effective_date"))
    return (dates[0], dates[-1]) if dates else (None, None)


def quality_for_date(date: str, path: Path = QUALITY_PATH) -> str:
    if not path.exists():
        return "unavailable"
    rows = []
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    eligible = [row for row in rows if row.get("date", "") <= date]
    return eligible[-1]["quality_flag"] if eligible else "unavailable"


def reconstruct_from_anchor(date: str, anchor_members: set[str] | None = None) -> MembershipResult:
    changes = load_changes()
    start, end = coverage_bounds(changes)
    if not start or date < start:
        return MembershipResult(date, [], "unavailable", f"Requested date {date} is before earliest event {start or 'not_available'}.")
    if anchor_members is None:
        return MembershipResult(
            date,
            [],
            "insufficient",
            "No verified full constituent snapshot is bundled; refusing to backfill from a current-only universe.",
        )
    members = set(anchor_members)
    for row in sorted(changes, key=lambda r: r["effective_date"], reverse=True):
        if row["effective_date"] <= date:
            break
        if row.get("added_ticker"):
            members.discard(row["added_ticker"])
        if row.get("removed_ticker"):
            members.add(row["removed_ticker"])
    return MembershipResult(date, sorted(members), quality_for_date(date), "")

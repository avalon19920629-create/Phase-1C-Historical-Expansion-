from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .normalize import event_key
from .reconstruct import load_changes

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports/reconstruction_validation.md"
QUALITY_PATH = ROOT / "artifacts/reconstruction_quality.csv"
COVERAGE_PATH = ROOT / "artifacts/membership_change_coverage_by_year.csv"
SNAPSHOT_COMPARISON_PATH = ROOT / "artifacts/snapshot_comparison.csv"
CONFLICT_PATH = ROOT / "artifacts/membership_change_conflicts.csv"


def validation_metrics(changes: list[dict[str, str]] | None = None) -> dict[str, object]:
    rows = changes if changes is not None else load_changes()
    dates = sorted(row["effective_date"] for row in rows if row.get("effective_date"))
    years = Counter(row["effective_date"][:4] for row in rows if row.get("effective_date"))
    sources = Counter(row.get("source", "") or "unknown" for row in rows)
    confidence = Counter(row.get("confidence", "") or "unknown" for row in rows)
    keys = Counter(event_key(row) for row in rows)
    conflict_count = 0
    if CONFLICT_PATH.exists():
        with CONFLICT_PATH.open(newline="") as handle:
            conflict_count = max(0, sum(1 for _ in csv.DictReader(handle)))
    return {
        "membership_changes_rows": len(rows),
        "earliest_effective_date": dates[0] if dates else "not_available",
        "latest_effective_date": dates[-1] if dates else "not_available",
        "events_by_year": dict(sorted(years.items())),
        "events_by_source": dict(sorted(sources.items())),
        "events_by_confidence": dict(sorted(confidence.items())),
        "duplicate_event_count": sum(count - 1 for count in keys.values() if count > 1),
        "conflict_count": conflict_count,
        "blank_added_count": sum(1 for row in rows if not row.get("added_ticker")),
        "blank_removed_count": sum(1 for row in rows if not row.get("removed_ticker")),
        "supported_reconstruction_start_date": dates[0] if dates and dates[0] <= "2010-01-01" else "target_unmet",
        "supported_reconstruction_end_date": dates[-1] if dates else "not_available",
    }


def write_coverage_by_year(metrics: dict[str, object], path: Path = COVERAGE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "event_count"])
        writer.writeheader()
        for year, count in (metrics["events_by_year"] or {}).items():
            writer.writerow({"year": year, "event_count": count})


def write_quality(metrics: dict[str, object], path: Path = QUALITY_PATH) -> None:
    fields = ["date", "constituent_count", "expected_count", "missing_count", "duplicate_count", "source_coverage", "quality_flag", "notes"]
    rows = []
    earliest = str(metrics["earliest_effective_date"])
    latest = str(metrics["latest_effective_date"])
    if earliest != "not_available":
        rows.append({
            "date": "1900-01-01",
            "constituent_count": "not_reconstructed",
            "expected_count": 500,
            "missing_count": "unknown",
            "duplicate_count": metrics["duplicate_event_count"],
            "source_coverage": "none",
            "quality_flag": "unavailable",
            "notes": f"Before earliest event {earliest}; do not use current constituents as history.",
        })
        rows.append({
            "date": earliest,
            "constituent_count": "not_reconstructed",
            "expected_count": 500,
            "missing_count": "unknown",
            "duplicate_count": metrics["duplicate_event_count"],
            "source_coverage": "selected_change_events",
            "quality_flag": "medium_for_event_history_only",
            "notes": "Change coverage exists from this date, but no full verified anchor snapshot is bundled.",
        })
        rows.append({
            "date": latest,
            "constituent_count": "not_reconstructed",
            "expected_count": 500,
            "missing_count": "unknown",
            "duplicate_count": metrics["duplicate_event_count"],
            "source_coverage": "selected_change_events",
            "quality_flag": "medium_for_event_history_only",
            "notes": "Latest bundled selected-change event.",
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot_comparison(path: Path = SNAPSHOT_COMPARISON_PATH) -> None:
    fields = ["date", "reconstructed_count", "snapshot_count", "overlap_count", "missing_from_reconstruction", "extra_in_reconstruction", "quality_flag", "notes"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "date": "not_available",
            "reconstructed_count": "not_available",
            "snapshot_count": "not_available",
            "overlap_count": "not_available",
            "missing_from_reconstruction": "not_available",
            "extra_in_reconstruction": "not_available",
            "quality_flag": "not_available",
            "notes": "No full public snapshot source was ingested by default in Phase 1C.",
        })


def write_validation_report(metrics: dict[str, object], path: Path = REPORT_PATH) -> None:
    lines = ["# Reconstruction Validation", ""]
    for key in [
        "membership_changes_rows", "earliest_effective_date", "latest_effective_date", "duplicate_event_count",
        "conflict_count", "blank_added_count", "blank_removed_count", "supported_reconstruction_start_date",
        "supported_reconstruction_end_date",
    ]:
        lines.append(f"- **{key}**: {metrics[key]}")
    lines.extend(["", "## Events by Year", "", "| Year | Events |", "| --- | ---: |"])
    for year, count in metrics["events_by_year"].items():
        lines.append(f"| {year} | {count} |")
    lines.extend(["", "## Events by Source", "", "| Source | Events |", "| --- | ---: |"])
    for source, count in metrics["events_by_source"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(["", "## Events by Confidence", "", "| Confidence | Events |", "| --- | ---: |"])
    for conf, count in metrics["events_by_confidence"].items():
        lines.append(f"| {conf} | {count} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def run_validation() -> dict[str, object]:
    metrics = validation_metrics()
    write_coverage_by_year(metrics)
    write_quality(metrics)
    write_snapshot_comparison()
    write_validation_report(metrics)
    return metrics

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .normalize import CHANGE_FIELDS, merge_changes, write_changes

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data/raw/seed/wikipedia_selected_changes_seed.csv"
MANUAL_PATH = ROOT / "data/raw/manual/membership_changes_manual.csv"
GITHUB_CHANGES_PATH = ROOT / "data/raw/github/fja_sp500_changes_since_2020_06.csv"
PROCESSED_PATH = ROOT / "data/processed/membership_changes.csv"
CONFLICT_PATH = ROOT / "artifacts/membership_change_conflicts.csv"
MANIFEST_PATH = ROOT / "artifacts/source_manifest.csv"

MANIFEST_FIELDS = [
    "source_name",
    "source_url",
    "accessed_at",
    "license_terms_uncertain",
    "fields_used",
    "date_range",
    "rows_extracted",
    "known_limitations",
]


@dataclass
class SourceResult:
    name: str
    url: str
    rows: list[dict[str, str]]
    license_terms_uncertain: bool
    fields_used: str
    known_limitations: str

    @property
    def date_range(self) -> str:
        dates = sorted(row.get("effective_date", "") for row in self.rows if row.get("effective_date"))
        return f"{dates[0]}..{dates[-1]}" if dates else "not_available"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def wikipedia_selected_changes(path: Path = SEED_PATH) -> SourceResult:
    return SourceResult(
        name="Wikipedia selected changes bundled seed",
        url="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#Selected_changes_to_the_list_of_S&P_500_components",
        rows=read_csv_rows(path),
        license_terms_uncertain=False,
        fields_used=",".join(CHANGE_FIELDS),
        known_limitations="Wikipedia explicitly labels this table as selected changes, so it is not guaranteed complete.",
    )


def bundled_seed_changes(path: Path = SEED_PATH) -> SourceResult:
    result = wikipedia_selected_changes(path)
    result.name = "Bundled seed changes"
    return result


def manual_changes(path: Path = MANUAL_PATH) -> SourceResult:
    rows = read_csv_rows(path)
    missing = [idx for idx, row in enumerate(rows, start=2) if not row.get("source_url") or not row.get("verified_at")]
    if missing:
        raise ValueError(f"Manual rows missing source_url or verified_at at CSV lines: {missing}")
    return SourceResult(
        name="Local manual reviewed CSV",
        url=str(path),
        rows=rows,
        license_terms_uncertain=False,
        fields_used=",".join(CHANGE_FIELDS),
        known_limitations="Only rows manually placed in data/raw/manual are included.",
    )


def github_csv_changes(path: Path | None = GITHUB_CHANGES_PATH) -> SourceResult:
    compact_rows = read_csv_rows(path) if path else []
    rows: list[dict[str, str]] = []
    for compact in compact_rows:
        added = [item.strip() for item in (compact.get("add") or "").split(",") if item.strip()]
        removed = [item.strip() for item in (compact.get("remove") or "").split(",") if item.strip()]
        for idx in range(max(len(added), len(removed))):
            rows.append({
                "effective_date": compact.get("date", ""),
                "added_ticker": added[idx] if idx < len(added) else "",
                "removed_ticker": removed[idx] if idx < len(removed) else "",
                "reason": "Ticker-level change from fja05680 sp500_changes_since_2019.csv",
                "source": "Public GitHub fja05680/sp500 changes",
                "source_url": "https://github.com/fja05680/sp500/blob/master/sp500_changes_since_2019.csv",
                "verified_at": "2026-06-03",
                "confidence": "medium",
                "notes": "MIT repository; compact ticker-only changes since 2019. Provenance notes in source README.",
            })
    return SourceResult(
        name="Public GitHub CSV changes",
        url="https://github.com/fja05680/sp500/blob/master/sp500_changes_since_2019.csv",
        rows=rows,
        license_terms_uncertain=False,
        fields_used="date,add,remove converted to membership change schema",
        known_limitations="Ticker-only compact changes; security names and detailed reasons are not present in the compact CSV. Repository README notes manual updates from Wikipedia/news and original historical data provenance limitations.",
    )


def snapshot_to_membership_changes(snapshots: dict[str, set[str]], source: str, source_url: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    dates = sorted(snapshots)
    for previous, current in zip(dates, dates[1:]):
        added = sorted(snapshots[current] - snapshots[previous])
        removed = sorted(snapshots[previous] - snapshots[current])
        for idx in range(max(len(added), len(removed))):
            rows.append(
                {
                    "effective_date": current,
                    "added_ticker": added[idx] if idx < len(added) else "",
                    "removed_ticker": removed[idx] if idx < len(removed) else "",
                    "reason": "Converted from historical constituent snapshot delta",
                    "source": source,
                    "source_url": source_url,
                    "verified_at": datetime.now(timezone.utc).date().isoformat(),
                    "confidence": "medium",
                    "notes": "Ticker-only snapshot delta; no row-level reason in snapshot source.",
                }
            )
    return rows


def write_source_manifest(results: Iterable[SourceResult], path: Path = MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    accessed_at = datetime.now(timezone.utc).isoformat()
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "source_name": result.name,
                    "source_url": result.url,
                    "accessed_at": accessed_at,
                    "license_terms_uncertain": str(result.license_terms_uncertain).lower(),
                    "fields_used": result.fields_used,
                    "date_range": result.date_range,
                    "rows_extracted": len(result.rows),
                    "known_limitations": result.known_limitations,
                }
            )


def build_membership_changes() -> list[dict[str, str]]:
    results = [wikipedia_selected_changes(), manual_changes(), github_csv_changes()]
    rows: list[dict[str, str]] = []
    for result in results:
        rows.extend(result.rows)
    merged = merge_changes(rows, CONFLICT_PATH)
    write_changes(merged, PROCESSED_PATH)
    write_source_manifest(results)
    return merged

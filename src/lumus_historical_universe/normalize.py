from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

CHANGE_FIELDS = [
    "effective_date",
    "added_ticker",
    "added_security",
    "removed_ticker",
    "removed_security",
    "reason",
    "source",
    "source_url",
    "verified_at",
    "confidence",
    "notes",
    "added_original_ticker",
    "removed_original_ticker",
]


def normalize_date(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value!r}")


def normalize_ticker(value: str) -> str:
    text = (value or "").strip().upper()
    return text.replace("BRK.B", "BRK-B").replace("BF.B", "BF-B")


def normalize_change_row(row: dict[str, str]) -> dict[str, str]:
    out = {field: (row.get(field) or "").strip() for field in CHANGE_FIELDS}
    out["effective_date"] = normalize_date(out["effective_date"])
    out["added_original_ticker"] = out["added_original_ticker"] or out["added_ticker"]
    out["removed_original_ticker"] = out["removed_original_ticker"] or out["removed_ticker"]
    out["added_ticker"] = normalize_ticker(out["added_ticker"])
    out["removed_ticker"] = normalize_ticker(out["removed_ticker"])
    out["confidence"] = (out["confidence"] or "medium").lower()
    return out


def event_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("effective_date", ""), row.get("added_ticker", ""), row.get("removed_ticker", ""))


def rows_disagree(left: dict[str, str], right: dict[str, str]) -> bool:
    comparable = ["added_security", "removed_security", "reason", "source_url", "confidence"]
    return any((left.get(k) or "") != (right.get(k) or "") for k in comparable)


def merge_changes(rows: Iterable[dict[str, str]], conflict_path: Path | None = None) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        norm = normalize_change_row(row)
        if norm["effective_date"]:
            grouped[event_key(norm)].append(norm)

    merged: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    for key, group in grouped.items():
        first = group[0]
        disagreement = any(rows_disagree(first, other) for other in group[1:])
        if disagreement:
            for item in group:
                conflicts.append(item | {"conflict_key": "|".join(key)})
            merged.extend(group)
        else:
            merged.append(first)

    merged.sort(key=lambda r: (r["effective_date"], r["added_ticker"], r["removed_ticker"], r["source"]))
    if conflict_path:
        conflict_path.parent.mkdir(parents=True, exist_ok=True)
        fields = CHANGE_FIELDS + ["conflict_key"]
        with conflict_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows([{field: row.get(field, "") for field in fields} for row in conflicts])
    return merged


def write_changes(rows: Iterable[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHANGE_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CHANGE_FIELDS} for row in rows])

from __future__ import annotations

from .sources import build_membership_changes
from .validate import run_validation


def main() -> None:
    rows = build_membership_changes()
    metrics = run_validation()
    print(f"built {len(rows)} rows; earliest={metrics['earliest_effective_date']}; latest={metrics['latest_effective_date']}")

if __name__ == "__main__":
    main()

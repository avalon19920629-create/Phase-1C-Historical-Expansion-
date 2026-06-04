from pathlib import Path

import pytest

from lumus_historical_universe.sources import manual_changes, snapshot_to_membership_changes, wikipedia_selected_changes


def test_seed_source_has_rows_before_2010():
    result = wikipedia_selected_changes()
    assert len(result.rows) > 0
    assert min(row["effective_date"] for row in result.rows if row.get("effective_date")) <= "2010-01-01"


def test_manual_rows_require_source_url_and_verified_at(tmp_path):
    path = tmp_path / "membership_changes_manual.csv"
    path.write_text("effective_date,added_ticker,removed_ticker,source_url,verified_at\n2018-01-01,A,B,,\n")
    with pytest.raises(ValueError):
        manual_changes(path)


def test_snapshot_to_membership_changes_converter():
    rows = snapshot_to_membership_changes({"2018-01-01": {"A", "B"}, "2018-02-01": {"B", "C"}}, "snapshot", "url")
    assert rows[0]["effective_date"] == "2018-02-01"
    assert {rows[0]["added_ticker"], rows[0]["removed_ticker"]} == {"C", "A"}

from lumus_historical_universe.normalize import merge_changes, normalize_change_row


def test_ticker_normalization_preserves_originals():
    row = normalize_change_row({"effective_date": "May 1, 2014", "added_ticker": "BRK.B", "removed_ticker": "BF.B"})
    assert row["effective_date"] == "2014-05-01"
    assert row["added_ticker"] == "BRK-B"
    assert row["removed_ticker"] == "BF-B"
    assert row["added_original_ticker"] == "BRK.B"
    assert row["removed_original_ticker"] == "BF.B"


def test_conflicting_duplicate_events_written(tmp_path):
    conflicts = tmp_path / "conflicts.csv"
    rows = [
        {"effective_date": "2018-01-01", "added_ticker": "A", "removed_ticker": "B", "reason": "one", "source_url": "u", "verified_at": "2026-06-03"},
        {"effective_date": "2018-01-01", "added_ticker": "A", "removed_ticker": "B", "reason": "two", "source_url": "u", "verified_at": "2026-06-03"},
    ]
    merged = merge_changes(rows, conflicts)
    assert len(merged) == 2
    assert conflicts.exists()
    assert "one" in conflicts.read_text()
    assert "two" in conflicts.read_text()

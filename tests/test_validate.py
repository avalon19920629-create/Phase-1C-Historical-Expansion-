from lumus_historical_universe.reconstruct import load_changes
from lumus_historical_universe.validate import validation_metrics


def test_processed_membership_changes_has_rows_and_target_met():
    rows = load_changes()
    assert len(rows) > 0
    assert min(row["effective_date"] for row in rows) <= "2010-01-01"


def test_validation_metrics_include_required_fields_and_duplicates():
    rows = [
        {"effective_date": "2018-01-01", "added_ticker": "A", "removed_ticker": "B", "source": "x", "confidence": "medium"},
        {"effective_date": "2018-01-01", "added_ticker": "A", "removed_ticker": "B", "source": "x", "confidence": "medium"},
        {"effective_date": "2018-02-01", "added_ticker": "", "removed_ticker": "C", "source": "y", "confidence": "low"},
    ]
    metrics = validation_metrics(rows)
    assert metrics["duplicate_event_count"] == 1
    assert metrics["blank_added_count"] == 1
    assert metrics["events_by_year"] == {"2018": 3}
    assert "supported_reconstruction_start_date" in metrics
